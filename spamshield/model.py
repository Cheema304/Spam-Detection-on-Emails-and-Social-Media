from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json
import math
import time

import joblib

from .preprocess import clean_text


class SpamModel:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.reload()

    def reload(self):
        self.pipelines = joblib.load(self.model_dir / "pipelines.joblib")
        self.metadata = json.loads((self.model_dir / "metadata.json").read_text(encoding="utf-8"))
        self.evaluation = json.loads((self.model_dir / "evaluation.json").read_text(encoding="utf-8"))
        self.details = json.loads((self.model_dir / "evaluation_details.json").read_text(encoding="utf-8"))
        self.active_key = self.metadata["active_key"]
        self.pipeline = self.pipelines[self.active_key]
        self.model_version = self.metadata.get("model_version", "unknown")
        return self

    def activate(self, key: str):
        if key not in self.pipelines:
            raise ValueError("Unknown model configuration")
        chosen = next((r for r in self.evaluation if r["key"] == key), None)
        if chosen is None:
            raise ValueError("Evaluation result for model configuration is missing")
        self.active_key = key
        self.pipeline = self.pipelines[key]
        self.metadata["active_key"] = key
        self.metadata["active_vectorizer"] = chosen["vectorizer"]
        self.metadata["active_model"] = chosen["model"]
        self.metadata["active_metrics"] = chosen
        (self.model_dir / "metadata.json").write_text(json.dumps(self.metadata, indent=2), encoding="utf-8")

    def _spam_probability(self, cleaned: str) -> float:
        classes = list(self.pipeline.classes_)
        if hasattr(self.pipeline, "predict_proba"):
            probs = self.pipeline.predict_proba([cleaned])[0]
            return float(probs[classes.index(1)])
        score = float(self.pipeline.decision_function([cleaned])[0])
        return 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, score))))

    def _signals(self, cleaned: str, limit: int = 6):
        try:
            vectorizer = self.pipeline.named_steps["vectorizer"]
            classifier = self.pipeline.named_steps["classifier"]
            if not hasattr(classifier, "coef_"):
                return []
            vector = vectorizer.transform([cleaned])
            feature_names = vectorizer.get_feature_names_out()
            coefs = classifier.coef_[0]
            indices = vector.nonzero()[1]
            scored = []
            for idx in indices:
                contribution = float(vector[0, idx]) * float(coefs[idx])
                if contribution > 0:
                    scored.append((contribution, feature_names[idx]))
            scored.sort(reverse=True)
            return [term for _, term in scored[:limit]]
        except Exception:
            return []

    def predict(self, text: str, source_type: str = "Email") -> dict:
        started = time.perf_counter()
        cleaned = clean_text(text)
        spam_probability = self._spam_probability(cleaned)
        label = "Spam" if spam_probability >= 0.5 else "Not Spam"
        confidence = spam_probability if label == "Spam" else 1.0 - spam_probability
        if spam_probability >= 0.80:
            risk = "High"
        elif spam_probability >= 0.50:
            risk = "Medium"
        else:
            risk = "Low"
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return {
            "source_type": source_type,
            "raw_text": text,
            "cleaned_text": cleaned,
            "prediction": label,
            "confidence": round(confidence * 100.0, 2),
            "spam_probability": round(spam_probability * 100.0, 2),
            "risk_level": risk,
            "signals": self._signals(cleaned),
            "processing_ms": round(elapsed_ms, 2),
            "model_version": self.model_version,
            "active_model_key": self.active_key,
            "active_model": self.metadata.get("active_model"),
            "active_vectorizer": self.metadata.get("active_vectorizer"),
            "created_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        }
