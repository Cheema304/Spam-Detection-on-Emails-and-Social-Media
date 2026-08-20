import json
import sys
import threading
import unittest
import tempfile
import tarfile
import zipfile
import io
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from spamshield.preprocess import clean_text
from spamshield.security import validate_message
from spamshield.model import SpamModel
from spamshield.datasets import _parse_spamassassin, _parse_youtube
from spamshield import server as server_module


class DatasetParserTests(unittest.TestCase):
    def test_spamassassin_archive_parser(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sample.tar.bz2"
            raw = b"Subject: Test offer\nContent-Type: text/plain; charset=utf-8\n\nClaim this offer now."
            with tarfile.open(path, "w:bz2") as tf:
                info = tarfile.TarInfo("spam/0001")
                info.size = len(raw)
                tf.addfile(info, io.BytesIO(raw))
            rows = _parse_spamassassin(path, "spam")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source"], "Email")
            self.assertEqual(rows[0]["label"], "spam")
            self.assertIn("Test offer", rows[0]["text"])

    def test_youtube_zip_parser(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "youtube.zip"
            csv_text = "COMMENT_ID,AUTHOR,DATE,CONTENT,CLASS\n1,User,2020-01-01,subscribe to my channel,1\n2,User2,2020-01-02,great video,0\n"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("Youtube01-Psy.csv", csv_text)
            rows = _parse_youtube(path)
            self.assertEqual(len(rows), 2)
            self.assertEqual({r["source"] for r in rows}, {"Social Media"})
            self.assertEqual({r["label"] for r in rows}, {"spam", "ham"})



class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = SpamModel(ROOT / "model")

    def test_preprocessing_tokens_urls(self):
        cleaned = clean_text("Contact user@example.com then visit https://example.com for $500")
        self.assertIn("emailtoken", cleaned)
        self.assertIn("urltoken", cleaned)
        self.assertIn("currencytoken", cleaned)
        self.assertIn("numtoken", cleaned)

    def test_validation(self):
        self.assertFalse(validate_message("   ")[0])
        self.assertTrue(validate_message("normal message")[0])
        self.assertFalse(validate_message("x" * 8001)[0])

    def test_real_dataset_metadata(self):
        m = self.model.metadata
        self.assertEqual(m["dataset_kind"], "real_public_data")
        self.assertGreater(m["dataset_rows"], 4000)
        self.assertGreater(m["email_spam_rows"] + m["email_ham_rows"], 1000)
        self.assertGreater(m["social_spam_rows"] + m["social_ham_rows"], 1000)

    def test_eight_live_model_results(self):
        self.assertEqual(len(self.model.evaluation), 8)
        keys = {r["key"] for r in self.model.evaluation}
        self.assertEqual(len(keys), 8)
        self.assertIn(self.model.active_key, keys)

    def test_metrics_are_recomputed_values(self):
        f1s = {round(float(r["f1"]), 4) for r in self.model.evaluation}
        self.assertGreater(len(f1s), 1, "All F1 values are identical; expected real benchmark variation")
        for row in self.model.evaluation:
            for metric in ["accuracy", "precision", "recall", "f1", "roc_auc"]:
                self.assertGreaterEqual(row[metric], 0)
                self.assertLessEqual(row[metric], 1)

    def test_prediction_shape(self):
        r = self.model.predict("Urgent prize notification: click https://example.com to claim your reward", "Email")
        self.assertIn(r["prediction"], {"Spam", "Not Spam"})
        self.assertGreaterEqual(r["spam_probability"], 0)
        self.assertLessEqual(r["spam_probability"], 100)
        self.assertEqual(r["active_model_key"], self.model.active_key)

    def test_model_activation_switch(self):
        original = self.model.active_key
        alternate = next(r["key"] for r in self.model.evaluation if r["key"] != original)
        try:
            self.model.activate(alternate)
            self.assertEqual(self.model.active_key, alternate)
            self.assertEqual(self.model.metadata["active_key"], alternate)
        finally:
            self.model.activate(original)
        self.assertEqual(self.model.active_key, original)

    def test_static_project_design_charts_exist(self):
        for name in ["architecture.png", "risk_matrix.png", "assessment_timeline.png"]:
            p = ROOT / "web" / "static" / "charts" / name
            self.assertTrue(p.is_file())
            self.assertGreater(p.stat().st_size, 1000)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server_module.DB.clear()
        cls.server = server_module.make_server("127.0.0.1", 0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=3)
        server_module.DB.clear()

    def get(self, path):
        with urlopen(self.base + path, timeout=20) as r:
            return r.status, r.read(), r.headers

    def test_all_pages(self):
        for path in ["/", "/detect", "/history", "/analytics", "/models", "/about"]:
            status, body, headers = self.get(path)
            self.assertEqual(status, 200, path)
            self.assertIn(b"SpamShield", body)
            self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")

    def test_live_svg_charts(self):
        for name in ["dataset", "model-comparison", "metrics", "confusion", "roc", "channels", "usage"]:
            status, body, headers = self.get(f"/live-chart/{name}.svg")
            self.assertEqual(status, 200, name)
            self.assertIn(b"<svg", body[:1000])
            self.assertIn("image/svg+xml", headers.get("Content-Type", ""))
            self.assertIn("no-store", headers.get("Cache-Control", ""))

    def test_health_api_real_data(self):
        status, body, _ = self.get("/api/health")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["dataset_kind"], "real_public_data")
        self.assertTrue(payload["active_model"])

    def test_model_evaluation_api(self):
        status, body, _ = self.get("/api/model-evaluation")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(len(payload["evaluation"]), 8)
        self.assertIn("confusion_matrix", payload["active_details"])

    def test_predict_api_persists(self):
        data = json.dumps({"text": "Congratulations! Claim your free prize now at http://claim-now.example", "source_type": "Email"}).encode()
        req = Request(self.base + "/api/predict", data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=20) as r:
            payload = json.loads(r.read())
        self.assertIn(payload["prediction"], {"Spam", "Not Spam"})
        self.assertIn("active_model", payload)
        self.assertNotIn("raw_text", payload)
        self.assertGreaterEqual(len(server_module.DB.recent()), 1)

    def test_detect_form_persists(self):
        before = len(server_module.DB.recent(250))
        data = urlencode({"message": "Hi team, the project meeting is Friday at 2 PM.", "source_type": "Email"}).encode()
        req = Request(self.base + "/detect", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        with urlopen(req, timeout=20) as r:
            body = r.read()
        self.assertIn(b"ANALYSIS RESULT", body)
        self.assertGreater(len(server_module.DB.recent(250)), before)

    def test_empty_api_rejected(self):
        data = json.dumps({"text": ""}).encode()
        req = Request(self.base + "/api/predict", data=data, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req, timeout=10)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
