# SpamShield AI — ICT942 Cyber Security Project

## Spam Detection on Emails and Social Media

This edition uses **real labelled public datasets** and **live model-evaluation graphics**. It does not ship hard-coded/demo benchmark values.

### Real datasets used

**Email — Apache SpamAssassin Public Corpus**
- Easy Ham archive: `20030228_easy_ham.tar.bz2`
- Spam archive: `20030228_spam.tar.bz2`
- Source: https://spamassassin.apache.org/old/publiccorpus/

**Social Media — UCI YouTube Spam Collection**
- Five labelled YouTube comment CSV datasets
- 1,956 real comments in the original UCI collection
- DOI: `10.24432/C58885`
- License: CC BY 4.0
- Source: https://archive.ics.uci.edu/dataset/380/youtube+spam+collection

On first run, the project downloads the source archives, parses them, deduplicates text, builds `data/real_combined.csv`, and trains the ML pipelines locally.

## What is live

The following are generated from the **current project state**, not attached screenshots:

- real dataset distribution by Email/Social Media and Spam/Ham
- F1 comparison for all eight pipelines
- Accuracy / Precision / Recall / F1 comparison
- active-model confusion matrix
- active-model ROC curve
- active-model Email-vs-Social-Media performance
- live application usage by channel from SQLite

Matplotlib renders these charts as SVG through `/live-chart/*.svg`. The server sends `Cache-Control: no-store`, so a refreshed Analytics page requests fresh graph output.

## Model benchmark

Two vectorisation approaches:
- Bag of Words
- TF-IDF

Four classifiers for each vectoriser:
- Multinomial Naive Bayes
- Logistic Regression
- Calibrated Linear SVM
- Random Forest

Total: **8 pipelines**.

The system ranks all pipelines by F1, ROC AUC, precision and accuracy. The best pipeline is activated automatically after retraining. The Model Lab lets you activate any of the eight evaluated models; live predictions and active-model charts immediately follow the selected model.

## Reproducible evaluation

- source-aware + class-aware stratified hold-out split
- random state: 42
- default test size: 25%
- dataset SHA-256 stored in `model/metadata.json`
- full model table in `model/evaluation.json`
- per-model confusion matrices, ROC points and channel metrics in `model/evaluation_details.json`
- all trained pipelines stored in `model/pipelines.joblib`

## Run on Windows

Double-click:

```text
run_windows.bat
```

The script creates `.venv`, installs dependencies if required, performs first-time real-data setup/training when needed, and launches `run.py`.

Optional Windows helpers:
- `setup_real_data_windows.bat` — download real data, train all models, then run the full tests.
- `retrain_real_data_windows.bat` — retrain from the existing real combined dataset and rerun tests.

On the first run, `run.py` automatically performs:

```text
scripts/fetch_real_data.py
scripts/train.py
```

Then open:

```text
http://127.0.0.1:8080
```

## Manual setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python scripts\fetch_real_data.py
python scripts\train.py
python run.py
```

## Retrain

From the UI: **Model Lab → Retrain all 8 models on real data**

Or command line:

```bash
python scripts\train.py
```

To force fresh downloads:

```bash
python scripts\fetch_real_data.py --force
python scripts\train.py
```

## Tests

```bash
python scripts\run_tests.py
```

Tests cover preprocessing, validation, real-dataset metadata, eight-model evaluation, metric variability, live SVG Matplotlib endpoints, pages, APIs, database persistence and security headers.

## Key routes

- `/` Dashboard
- `/detect` Live detection
- `/history` Prediction history
- `/analytics` Live Matplotlib analytics
- `/models` Model Evaluation Lab + model activation/retraining
- `/about` Architecture
- `/api/health`
- `/api/stats`
- `/api/model-evaluation`
- `/api/predict`
- `/live-chart/<chart>.svg`

## Project evidence

The `docs/` directory includes requirements, traceability, risk, cybersecurity assessment, Jira backlog, Git workflow and portfolio working structures aligned to ICT942 Weeks 1–5.
