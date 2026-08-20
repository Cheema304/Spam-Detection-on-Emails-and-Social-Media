# Project Validation Procedure

The release intentionally does **not** bundle precomputed ML benchmark numbers. First-time setup downloads the real public datasets and generates the model/evaluation artefacts on the user's machine.

## Required validation sequence

```bash
python scripts/fetch_real_data.py
python scripts/train.py
python scripts/run_tests.py
python run.py
```

## Automated coverage

The test suite verifies:
- preprocessing tokens and input validation
- real-dataset metadata and both project channels (Email + Social Media)
- eight distinct evaluated ML pipelines
- computed metric ranges and benchmark variation
- active-model switching
- dynamic Matplotlib SVG chart endpoints
- Dashboard, Detector, History, Analytics, Model Lab and Architecture pages
- security response headers
- health and model-evaluation APIs
- prediction API
- form/API SQLite persistence
- invalid-input rejection

## Evidence to retain

After the real-data setup, capture the terminal output showing the complete test suite passes and screenshots of the Model Lab and Analytics pages. The model version, training time, dataset SHA-256 and current metrics are stored in `model/metadata.json` and `model/evaluation.json`.
