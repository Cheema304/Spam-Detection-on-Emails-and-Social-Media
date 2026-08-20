# Testing Evidence Guide

Run the complete automated test suite after the first real-data training:

```bash
python scripts/run_tests.py
```

The runner automatically performs real-data setup/training if the required model artefacts do not yet exist.

For assessment evidence, retain:
- terminal screenshot showing the full test suite result
- Model Lab screenshot showing all eight current pipeline metrics
- Analytics screenshots showing live dataset/model/confusion/ROC/channel charts
- History screenshot proving predictions persist in SQLite
- `/api/health` screenshot showing `dataset_kind: real_public_data`
- Jira task/bug IDs for defects discovered and corrected
- Git commit hashes for training, evaluation, chart and testing work

Do not reuse old screenshots after retraining: the project intentionally regenerates evaluation values and renders charts from the newest project state.
