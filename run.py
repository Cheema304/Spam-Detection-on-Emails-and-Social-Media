from pathlib import Path
import argparse
import importlib.util
import json
import subprocess
import sys
import threading
import webbrowser

ROOT = Path(__file__).resolve().parent
REQUIRED = {
    "sklearn": "scikit-learn",
    "joblib": "joblib",
    "matplotlib": "matplotlib",
    "numpy": "numpy",
}
missing = [pkg for mod, pkg in REQUIRED.items() if importlib.util.find_spec(mod) is None]
if missing:
    print("Missing Python packages:", ", ".join(missing))
    print("Install them with: python -m pip install -r requirements.txt")
    raise SystemExit(2)


def _real_model_ready():
    required = [
        ROOT / "model" / "pipelines.joblib",
        ROOT / "model" / "evaluation.json",
        ROOT / "model" / "evaluation_details.json",
        ROOT / "model" / "metadata.json",
    ]
    if not all(p.exists() for p in required):
        return False
    try:
        metadata = json.loads((ROOT / "model" / "metadata.json").read_text(encoding="utf-8"))
        return metadata.get("dataset_kind") == "real_public_data"
    except Exception:
        return False


if not _real_model_ready():
    print("\nSpamShield AI requires REAL labelled Email + Social Media data.")
    print("Downloading Apache SpamAssassin + UCI YouTube Spam Collection and training all 8 pipelines...")
    print("This first-time setup may take a few minutes depending on your internet connection and computer.\n")
    try:
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "fetch_real_data.py")], cwd=ROOT)
        subprocess.check_call([sys.executable, str(ROOT / "scripts" / "train.py")], cwd=ROOT)
    except subprocess.CalledProcessError:
        print("\nREAL-DATA SETUP FAILED.")
        print("Check your internet connection and run:")
        print("  python scripts\\fetch_real_data.py")
        print("  python scripts\\train.py")
        raise SystemExit(3)

from spamshield.server import make_server

parser = argparse.ArgumentParser(description="Run SpamShield AI")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=8080)
parser.add_argument("--no-browser", action="store_true")
args = parser.parse_args()

server = make_server(args.host, args.port)
url = f"http://{args.host}:{server.server_address[1]}"
print("\nSpamShield AI is running with REAL-DATA model evaluation")
print("Open:", url)
print("Press Ctrl+C to stop.\n")
if not args.no_browser:
    threading.Timer(.8, lambda: webbrowser.open(url)).start()
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nStopping SpamShield AI...")
finally:
    server.server_close()
