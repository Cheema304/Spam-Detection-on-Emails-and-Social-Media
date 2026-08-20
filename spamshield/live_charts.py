from __future__ import annotations

from io import BytesIO
from pathlib import Path
import json
import threading

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BG = "#0b1a2c"
PANEL = "#101f34"
TEXT = "#eef6ff"
MUTED = "#9cb1cb"
GRID = "#27415f"
CHART_LOCK = threading.Lock()

ACCENTS = ["#55e6a5", "#6aa9ff", "#ffc65c", "#ff7f91", "#b58cff", "#65d9e8", "#ff9d66", "#8de06d"]


def _base(figsize=(8, 4.8)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.title.set_color(TEXT)
    ax.grid(axis="y", color=GRID, alpha=.35, linewidth=.7)
    return fig, ax


def _svg(fig) -> bytes:
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="svg", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()


def dataset_distribution(metadata: dict) -> bytes:
    fig, ax = _base((8.2, 4.8))
    channels = ["Email", "Social Media"]
    ham = [metadata.get("email_ham_rows", 0), metadata.get("social_ham_rows", 0)]
    spam = [metadata.get("email_spam_rows", 0), metadata.get("social_spam_rows", 0)]
    x = np.arange(len(channels))
    width = .34
    b1 = ax.bar(x - width/2, ham, width, label="Ham / Not Spam", color=ACCENTS[1])
    b2 = ax.bar(x + width/2, spam, width, label="Spam", color=ACCENTS[3])
    ax.set_title("Real Dataset Distribution by Channel", fontweight="bold", pad=12)
    ax.set_ylabel("Messages")
    ax.set_xticks(x, channels)
    ax.legend(frameon=False, labelcolor=TEXT)
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x()+b.get_width()/2, b.get_height(), f"{int(b.get_height())}", ha="center", va="bottom", color=TEXT, fontsize=9, fontweight="bold")
    return _svg(fig)


def model_comparison(evaluation: list[dict], active_key: str) -> bytes:
    fig, ax = _base((11, 5.2))
    data = list(reversed(evaluation))
    names = [f"{r['vectorizer']} + {r['model']}" for r in data]
    vals = [r["f1"] for r in data]
    colors = [ACCENTS[0] if r["key"] == active_key else ACCENTS[1] for r in data]
    y = np.arange(len(data))
    bars = ax.barh(y, vals, color=colors)
    ax.set_yticks(y, names)
    ax.set_xlim(max(0, min(vals)-.08), 1.01)
    ax.set_xlabel("F1 score")
    ax.set_title("Live Benchmark — F1 Score by Pipeline", fontweight="bold", pad=12)
    for b, v in zip(bars, vals):
        ax.text(v + .004, b.get_y()+b.get_height()/2, f"{v:.3f}", va="center", color=TEXT, fontsize=9)
    return _svg(fig)


def metric_comparison(evaluation: list[dict]) -> bytes:
    fig, ax = _base((12, 5.4))
    data = evaluation
    names = [f"{r['vectorizer'][:3]}\n{r['model'].replace('Logistic Regression','LogReg').replace('Random Forest','RF').replace('Naive Bayes','NB').replace('Linear SVM','SVM')}" for r in data]
    x = np.arange(len(data))
    width = .19
    metrics = [("accuracy", "Accuracy"), ("precision", "Precision"), ("recall", "Recall"), ("f1", "F1")]
    for i, (key, label) in enumerate(metrics):
        ax.bar(x + (i-1.5)*width, [r[key] for r in data], width, label=label, color=ACCENTS[i])
    ax.set_title("Live Hold-out Metrics Across All Pipelines", fontweight="bold", pad=12)
    ax.set_ylim(0, 1.03)
    ax.set_xticks(x, names)
    ax.legend(ncols=4, frameon=False, labelcolor=TEXT, loc="lower center")
    return _svg(fig)


def confusion_matrix_chart(details: dict, active_key: str, active_name: str) -> bytes:
    cm = np.array(details[active_key]["confusion_matrix"], dtype=int)
    fig, ax = _base((6.3, 5.5))
    im = ax.imshow(cm, cmap="viridis")
    ax.grid(False)
    ax.set_title(f"Active Model Confusion Matrix\n{active_name}", fontweight="bold", pad=12)
    ax.set_xticks([0, 1], ["Ham", "Spam"])
    ax.set_yticks([0, 1], ["Ham", "Spam"])
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    threshold = cm.max()/2 if cm.size else 0
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black" if cm[i, j] > threshold else "white", fontsize=14, fontweight="bold")
    cbar = fig.colorbar(im, ax=ax, fraction=.046, pad=.04)
    cbar.ax.tick_params(colors=MUTED)
    return _svg(fig)


def roc_chart(details: dict, active_key: str, active_name: str) -> bytes:
    roc = details[active_key]["roc"]
    fig, ax = _base((7.2, 5.4))
    ax.plot(roc["fpr"], roc["tpr"], linewidth=2.2, color=ACCENTS[1], label=f"ROC AUC = {roc['auc']:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", linewidth=1.1, color=ACCENTS[3], alpha=.8, label="Random baseline")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.01)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title(f"Active Model ROC Curve\n{active_name}", fontweight="bold", pad=12)
    ax.legend(frameon=False, labelcolor=TEXT, loc="lower right")
    return _svg(fig)


def channel_performance(details: dict, active_key: str) -> bytes:
    channels = details[active_key].get("channel_metrics", {})
    fig, ax = _base((8.4, 4.8))
    names = [x for x in ["Email", "Social Media"] if x in channels]
    x = np.arange(len(names))
    width = .2
    metrics = [("accuracy", "Accuracy"), ("precision", "Precision"), ("recall", "Recall"), ("f1", "F1")]
    for i, (key, label) in enumerate(metrics):
        ax.bar(x + (i-1.5)*width, [channels[n][key] for n in names], width, label=label, color=ACCENTS[i])
    ax.set_title("Active Model Performance by Channel", fontweight="bold", pad=12)
    ax.set_xticks(x, names)
    ax.set_ylim(0, 1.03)
    ax.legend(ncols=4, frameon=False, labelcolor=TEXT, loc="lower center")
    return _svg(fig)


def live_usage(stats: dict) -> bytes:
    by_source = {r["source_type"]: int(r["count"]) for r in stats.get("by_source", [])}
    labels = ["Email", "Social Media", "API"]
    vals = [by_source.get(x, 0) for x in labels]
    fig, ax = _base((8, 4.6))
    bars = ax.bar(labels, vals, color=[ACCENTS[1], ACCENTS[0], ACCENTS[4]])
    ax.set_title("Live Application Usage by Channel", fontweight="bold", pad=12)
    ax.set_ylabel("Stored predictions")
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, b.get_height(), str(v), ha="center", va="bottom", color=TEXT, fontweight="bold")
    return _svg(fig)


def render(kind: str, model, stats: dict) -> bytes:
    # Matplotlib has global state; browsers request image resources concurrently.
    # Serialising chart rendering prevents cross-thread rendering races.
    with CHART_LOCK:
        evaluation = list(model.evaluation)
        metadata = dict(model.metadata)
        details = model.details
        active_key = model.active_key
        active_name = f"{metadata['active_vectorizer']} + {metadata['active_model']}"
        if kind == "dataset":
            return dataset_distribution(metadata)
        if kind == "model-comparison":
            return model_comparison(evaluation, active_key)
        if kind == "metrics":
            return metric_comparison(evaluation)
        if kind == "confusion":
            return confusion_matrix_chart(details, active_key, active_name)
        if kind == "roc":
            return roc_chart(details, active_key, active_name)
        if kind == "channels":
            return channel_performance(details, active_key)
        if kind == "usage":
            return live_usage(stats)
        raise KeyError(kind)
