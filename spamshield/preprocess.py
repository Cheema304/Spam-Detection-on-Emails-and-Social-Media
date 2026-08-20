import re

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)
SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Normalize text without executing or following any embedded content."""
    text = str(text or "").strip().lower()
    text = URL_RE.sub(" urltoken ", text)
    text = EMAIL_RE.sub(" emailtoken ", text)
    text = text.replace("£", " currencytoken ").replace("€", " currencytoken ").replace("$", " currencytoken ")
    text = re.sub(r"\b\d+(?:[.,]\d+)?\b", " numtoken ", text)
    text = re.sub(r"[^a-z0-9_!?\s]", " ", text)
    return SPACE_RE.sub(" ", text).strip()
