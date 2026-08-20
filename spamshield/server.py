from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, quote
import json
import mimetypes
import os
import threading

from .db import Database
from .model import SpamModel
from .security import SECURITY_HEADERS, MAX_BODY_BYTES, validate_message
from . import views
from .live_charts import render as render_live_chart

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
STATIC = WEB / "static"
MODEL_DIR = ROOT / "model"
DB_PATH = Path(os.environ.get("SPAMSHIELD_DB", str(ROOT / "spamshield.db")))

DB = Database(DB_PATH)
MODEL = SpamModel(MODEL_DIR)
TRAIN_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "SpamShield/2.0"

    def log_message(self, fmt, *args):
        print(f"[SpamShield] {self.address_string()} - {fmt % args}")

    def _send(self, status, body, content_type="text/html; charset=utf-8", headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for k, v in SECURITY_HEADERS.items():
            self.send_header(k, v)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, data):
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _redirect(self, location):
        self._send(303, b"", "text/plain; charset=utf-8", {"Location": location})

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body too large")
        return self.rfile.read(length)

    def _serve_static(self, path):
        relative = path[len("/static/"):]
        target = (STATIC / relative).resolve()
        try:
            target.relative_to(STATIC.resolve())
        except ValueError:
            return self._send(403, "Forbidden", "text/plain; charset=utf-8")
        if not target.is_file():
            return self._send(404, "Not found", "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        return self._send(200, target.read_bytes(), ctype, {"Cache-Control": "public, max-age=3600"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        try:
            if path.startswith("/static/"):
                return self._serve_static(path)
            if path.startswith("/live-chart/") and path.endswith(".svg"):
                kind = path[len("/live-chart/"):-4]
                try:
                    svg = render_live_chart(kind, MODEL, DB.stats())
                except KeyError:
                    return self._send(404, "Unknown chart", "text/plain; charset=utf-8")
                return self._send(200, svg, "image/svg+xml; charset=utf-8", {"Cache-Control": "no-store, max-age=0"})
            if path == "/":
                return self._send(200, views.dashboard(DB.stats(), DB.recent(), MODEL.metadata))
            if path == "/detect":
                return self._send(200, views.detect())
            if path == "/history":
                q = qs.get("q", [""])[0][:200]
                label = qs.get("label", [""])[0]
                source = qs.get("source", [""])[0]
                return self._send(200, views.history(DB.search(q, label, source), q, label, source))
            if path == "/analytics":
                return self._send(200, views.analytics(DB.stats(), MODEL.metadata))
            if path == "/models":
                notice = qs.get("notice", [""])[0][:300]
                return self._send(200, views.models(MODEL.evaluation, MODEL.metadata, notice))
            if path == "/about":
                return self._send(200, views.about(MODEL.metadata))
            if path == "/api/health":
                return self._json(200, {
                    "status": "ok",
                    "model_loaded": True,
                    "model_version": MODEL.model_version,
                    "dataset_kind": MODEL.metadata.get("dataset_kind"),
                    "active_model": MODEL.metadata.get("active_model"),
                    "active_vectorizer": MODEL.metadata.get("active_vectorizer"),
                })
            if path == "/api/stats":
                stats = DB.stats(); s = stats["summary"]
                return self._json(200, {
                    "total": s["total"], "spam": s["spam"], "not_spam": s["ham"],
                    "avg_processing_ms": round(float(s["avg_ms"] or 0), 2),
                    "model_version": MODEL.model_version,
                })
            if path == "/api/model-evaluation":
                return self._json(200, {
                    "metadata": MODEL.metadata,
                    "evaluation": MODEL.evaluation,
                    "active_details": MODEL.details.get(MODEL.active_key, {}),
                })
            return self._send(404, views.layout("404", "Page Not Found", '<section class="panel empty-state"><div class="empty-icon">404</div><b>Page not found</b><a class="button primary" href="/">Return to dashboard</a></section>'))
        except Exception as exc:
            self._send(500, views.layout("Error", "Application Error", f'<section class="panel"><div class="alert">An unexpected error occurred: {type(exc).__name__}. Check the console log.</div></section>'))
            print("GET error:", repr(exc))

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            raw = self._read_body()
        except ValueError as exc:
            return self._json(413, {"error": str(exc)})
        try:
            if parsed.path == "/detect":
                if "application/x-www-form-urlencoded" not in self.headers.get("Content-Type", ""):
                    return self._send(415, views.detect(error="Unsupported form content type."))
                form = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
                text = form.get("message", [""])[0]
                source = form.get("source_type", ["Email"])[0]
                if source not in {"Email", "Social Media"}:
                    source = "Email"
                valid, error = validate_message(text)
                if not valid:
                    return self._send(400, views.detect(error=error, message=text, source=source))
                result = MODEL.predict(text, source)
                DB.add_prediction(result)
                return self._send(200, views.detect(result=result, message=text, source=source))

            if parsed.path == "/models/activate":
                form = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
                key = form.get("key", [""])[0]
                MODEL.activate(key)
                return self._redirect("/models?notice=" + quote(f"Active model changed to {MODEL.metadata['active_vectorizer']} + {MODEL.metadata['active_model']}. Live predictions and active-model charts now use this pipeline."))

            if parsed.path == "/models/retrain":
                if not TRAIN_LOCK.acquire(blocking=False):
                    return self._redirect("/models?notice=" + quote("A retraining job is already running."))
                try:
                    from .datasets import build_real_dataset
                    from .training import train_and_evaluate
                    dataset = build_real_dataset()
                    train_and_evaluate(dataset)
                    MODEL.reload()
                finally:
                    TRAIN_LOCK.release()
                return self._redirect("/models?notice=" + quote(f"Retraining completed from real public datasets. New model version: {MODEL.model_version}. All evaluation charts have been refreshed."))

            if parsed.path == "/api/predict":
                if "application/json" not in self.headers.get("Content-Type", ""):
                    return self._json(415, {"error": "Content-Type must be application/json"})
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except Exception:
                    return self._json(400, {"error": "Invalid JSON body"})
                text = str(payload.get("text", ""))
                source = str(payload.get("source_type", "API"))
                if source not in {"Email", "Social Media", "API"}:
                    source = "API"
                valid, error = validate_message(text)
                if not valid:
                    return self._json(400, {"error": error})
                result = MODEL.predict(text, source)
                DB.add_prediction(result)
                public = {k: v for k, v in result.items() if k != "raw_text"}
                return self._json(200, public)

            return self._json(404, {"error": "Not found"})
        except Exception as exc:
            print("POST error:", repr(exc))
            return self._json(500, {"error": f"Internal server error: {type(exc).__name__}"})


def make_server(host="127.0.0.1", port=8080):
    return ThreadingHTTPServer((host, port), Handler)
