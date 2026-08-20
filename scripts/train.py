from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from spamshield.datasets import build_real_dataset
from spamshield.training import train_and_evaluate

parser = argparse.ArgumentParser(description="Train and evaluate all SpamShield AI pipelines")
parser.add_argument("--dataset", default="", help="CSV containing text,label,source; default uses real downloaded datasets")
parser.add_argument("--test-size", type=float, default=.25)
args = parser.parse_args()

if args.dataset:
    dataset = Path(args.dataset).resolve()
else:
    dataset = build_real_dataset()

print(f"Training from: {dataset}")
metadata = train_and_evaluate(dataset, test_size=args.test_size)
print("\nTraining complete.")
print("Best/active pipeline:", metadata["active_vectorizer"], "+", metadata["active_model"])
print("Model version:", metadata["model_version"])
print("Dataset rows:", metadata["dataset_rows"])
