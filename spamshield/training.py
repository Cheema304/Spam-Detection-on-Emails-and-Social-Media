from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score, roc_curve
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .preprocess import clean_text
from .datasets import SOURCE_INFO, dataset_summary

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"


def read_dataset(path: Path):
    rows = []
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {x.strip().lower() for x in (reader.fieldnames or [])}
        if not {"text", "label", "source"}.issubset(fields):
            raise ValueError("Dataset must contain text, label and source columns")
        for row in reader:
            raw_label = str(row.get("label", "")).strip().lower()
            if raw_label in {"spam", "1", "true", "yes"}:
                label = 1
            elif raw_label in {"ham", "not spam", "not_spam", "0", "false", "no"}:
                label = 0
            else:
                continue
            source = str(row.get("source", "")).strip()
            if source not in {"Email", "Social Media"}:
                continue
            text = str(row.get("text", "")).strip()
            if text:
                rows.append((clean_text(text), label, source))
    if len(rows) < 100:
        raise ValueError("At least 100 usable labelled rows are required")
    if {r[2] for r in rows} != {"Email", "Social Media"}:
        raise ValueError("Dataset must contain both Email and Social Media records")
    return rows


def model_key(vectorizer_name: str, model_name: str) -> str:
    def slug(s):
        return s.lower().replace("-", "_").replace(" ", "_")
    return f"{slug(vectorizer_name)}__{slug(model_name)}"


def build_pipeline(vectorizer_name: str, model_name: str):
    if vectorizer_name == "Bag of Words":
        vectorizer = CountVectorizer(ngram_range=(1, 2), min_df=2, max_df=.995, max_features=70000)
    elif vectorizer_name == "TF-IDF":
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=.995, sublinear_tf=True, max_features=70000)
    else:
        raise ValueError(vectorizer_name)

    if model_name == "Naive Bayes":
        classifier = MultinomialNB(alpha=.7)
    elif model_name == "Logistic Regression":
        classifier = LogisticRegression(max_iter=3000, class_weight="balanced", random_state=42)
    elif model_name == "Linear SVM":
        classifier = CalibratedClassifierCV(
            LinearSVC(class_weight="balanced", random_state=42),
            method="sigmoid", cv=3
        )
    elif model_name == "Random Forest":
        classifier = RandomForestClassifier(
            n_estimators=220, class_weight="balanced", random_state=42,
            n_jobs=-1, max_features="sqrt", min_samples_leaf=1
        )
    else:
        raise ValueError(model_name)
    return Pipeline([("vectorizer", vectorizer), ("classifier", classifier)])


def _scores(pipe, X):
    classes = list(pipe.classes_)
    if hasattr(pipe, "predict_proba"):
        probs = pipe.predict_proba(X)
        return np.asarray(probs[:, classes.index(1)], dtype=float)
    raw = np.asarray(pipe.decision_function(X), dtype=float)
    return 1.0 / (1.0 + np.exp(-np.clip(raw, -50, 50)))


def _metric_pack(y_true, pred, scores):
    result = {
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
    }
    try:
        result["roc_auc"] = float(roc_auc_score(y_true, scores))
    except ValueError:
        result["roc_auc"] = 0.0
    return result


def train_and_evaluate(dataset: Path, test_size: float = .25) -> dict:
    dataset = Path(dataset).resolve()
    rows = read_dataset(dataset)
    texts = np.array([r[0] for r in rows], dtype=object)
    labels = np.array([r[1] for r in rows], dtype=int)
    sources = np.array([r[2] for r in rows], dtype=object)
    strata = np.array([f"{src}|{label}" for src, label in zip(sources, labels)], dtype=object)

    X_train, X_test, y_train, y_test, src_train, src_test = train_test_split(
        texts, labels, sources, test_size=test_size, random_state=42, stratify=strata
    )

    configs = [
        (v, m)
        for v in ["Bag of Words", "TF-IDF"]
        for m in ["Naive Bayes", "Logistic Regression", "Linear SVM", "Random Forest"]
    ]
    results = []
    details = {}
    pipelines = {}

    for vectorizer_name, classifier_name in configs:
        key = model_key(vectorizer_name, classifier_name)
        pipe = build_pipeline(vectorizer_name, classifier_name)
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        scores = _scores(pipe, X_test)
        metrics = _metric_pack(y_test, pred, scores)
        row = {
            "key": key,
            "vectorizer": vectorizer_name,
            "model": classifier_name,
            **{k: round(v, 4) for k, v in metrics.items()},
        }
        results.append(row)
        pipelines[key] = pipe

        cm = confusion_matrix(y_test, pred, labels=[0, 1]).tolist()
        try:
            fpr, tpr, _ = roc_curve(y_test, scores)
        except ValueError:
            fpr, tpr = np.array([0.0, 1.0]), np.array([0.0, 1.0])

        channel_metrics = {}
        for channel in ["Email", "Social Media"]:
            mask = src_test == channel
            if int(mask.sum()) == 0:
                continue
            m = _metric_pack(y_test[mask], pred[mask], scores[mask])
            channel_metrics[channel] = {
                **{k: round(v, 4) for k, v in m.items()},
                "test_rows": int(mask.sum()),
                "spam_rows": int(y_test[mask].sum()),
                "ham_rows": int((y_test[mask] == 0).sum()),
            }

        details[key] = {
            "confusion_matrix": cm,
            "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "auc": float(metrics["roc_auc"])},
            "channel_metrics": channel_metrics,
        }
        print(
            f"{vectorizer_name:13} | {classifier_name:19} | "
            f"F1={row['f1']:.4f} | Acc={row['accuracy']:.4f} | AUC={row['roc_auc']:.4f}"
        )

    results.sort(key=lambda r: (r["f1"], r["roc_auc"], r["precision"], r["accuracy"]), reverse=True)
    best = results[0]
    active_key = best["key"]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipelines, MODEL_DIR / "pipelines.joblib")
    (MODEL_DIR / "evaluation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (MODEL_DIR / "evaluation_details.json").write_text(json.dumps(details, indent=2), encoding="utf-8")

    digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
    summary = dataset_summary(dataset)
    version = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    metadata = {
        "model_version": version,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_kind": "real_public_data",
        "dataset_file": dataset.name,
        "dataset_sha256": digest,
        "dataset_rows": int(summary["total"]),
        "spam_rows": int(summary["spam"]),
        "ham_rows": int(summary["ham"]),
        "email_spam_rows": int(summary["Email"]["spam"]),
        "email_ham_rows": int(summary["Email"]["ham"]),
        "social_spam_rows": int(summary["Social Media"]["spam"]),
        "social_ham_rows": int(summary["Social Media"]["ham"]),
        "test_rows": int(len(y_test)),
        "train_rows": int(len(y_train)),
        "test_size": float(test_size),
        "random_state": 42,
        "split_strategy": "stratified hold-out by source channel and class label",
        "best_key": best["key"],
        "active_key": active_key,
        "active_vectorizer": best["vectorizer"],
        "active_model": best["model"],
        "active_metrics": best,
        "data_sources": SOURCE_INFO,
        "evaluation_note": "Metrics are computed from the labelled hold-out set created from the downloaded public datasets. They are recalculated whenever the models are retrained.",
    }
    (MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
