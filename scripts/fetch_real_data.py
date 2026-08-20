from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from spamshield.datasets import build_real_dataset, dataset_summary, SOURCE_INFO

parser = argparse.ArgumentParser(description="Download and prepare the official public datasets used by SpamShield AI")
parser.add_argument("--force", action="store_true", help="Redownload source archives and rebuild the combined dataset")
args = parser.parse_args()

print("Preparing REAL labelled datasets for Email + Social Media spam detection...")
path = build_real_dataset(force_download=args.force)
summary = dataset_summary(path)
print(f"Combined dataset: {path}")
print(json.dumps(summary, indent=2))
print("Sources:")
for name, info in SOURCE_INFO.items():
    print(f" - {name}: {info['url']}")
