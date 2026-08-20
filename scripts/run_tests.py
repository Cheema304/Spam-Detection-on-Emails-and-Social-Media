from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
metadata_path = ROOT / "model" / "metadata.json"
ready = False
if metadata_path.exists():
    try:
        ready = json.loads(metadata_path.read_text(encoding="utf-8")).get("dataset_kind") == "real_public_data"
    except Exception:
        ready = False
if not ready:
    print("Real-data model artifacts are not ready. Running first-time data setup + training...")
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "fetch_real_data.py")], cwd=ROOT)
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "train.py")], cwd=ROOT)
raise SystemExit(subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"], cwd=ROOT))
