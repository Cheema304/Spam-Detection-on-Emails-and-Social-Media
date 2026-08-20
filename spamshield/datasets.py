from __future__ import annotations

from pathlib import Path
from email import policy
from email.parser import BytesParser
from html import unescape
import csv
import hashlib
import io
import re
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
COMBINED = DATA_DIR / "real_combined.csv"

SPAMASSASSIN_HAM_URLS = [
    "https://spamassassin.apache.org/old/publiccorpus/20030228_easy_ham.tar.bz2",
]
SPAMASSASSIN_SPAM_URLS = [
    "https://spamassassin.apache.org/old/publiccorpus/20030228_spam.tar.bz2",
]
YOUTUBE_URLS = [
    "https://archive.ics.uci.edu/static/public/380/youtube%2Bspam%2Bcollection.zip",
    "https://archive.ics.uci.edu/static/public/380/youtube+spam+collection.zip",
]

SOURCE_INFO = {
    "SpamAssassin": {
        "channel": "Email",
        "publisher": "Apache SpamAssassin Public Corpus",
        "url": "https://spamassassin.apache.org/old/publiccorpus/",
    },
    "UCI YouTube Spam Collection": {
        "channel": "Social Media",
        "publisher": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/dataset/380/youtube+spam+collection",
        "doi": "10.24432/C58885",
        "license": "CC BY 4.0",
    },
}


def _download(urls: list[str], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 1024:
        return destination
    last_error = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SpamShield-AI-ICT942/2.0"})
            with urllib.request.urlopen(req, timeout=90) as response, destination.open("wb") as out:
                while True:
                    block = response.read(1024 * 256)
                    if not block:
                        break
                    out.write(block)
            if destination.stat().st_size <= 1024:
                raise RuntimeError("Downloaded file is unexpectedly small")
            return destination
        except Exception as exc:
            last_error = exc
            if destination.exists():
                destination.unlink(missing_ok=True)
    raise RuntimeError(f"Could not download {destination.name}: {last_error}")


def _decode_bytes(data: bytes) -> str:
    for enc in ("utf-8", "windows-1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def _html_to_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\\s+", " ", unescape(value)).strip()


def _email_body(msg) -> str:
    pieces: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            ctype = part.get_content_type()
            if ctype not in {"text/plain", "text/html"}:
                continue
            disp = str(part.get("Content-Disposition", "")).lower()
            if "attachment" in disp:
                continue
            try:
                text = part.get_content()
            except Exception:
                payload = part.get_payload(decode=True) or b""
                text = _decode_bytes(payload)
            if ctype == "text/html":
                text = _html_to_text(str(text))
            pieces.append(str(text))
    else:
        try:
            text = msg.get_content()
        except Exception:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                text = _decode_bytes(payload)
            else:
                text = str(payload or "")
        if msg.get_content_type() == "text/html":
            text = _html_to_text(str(text))
        pieces.append(str(text))
    return "\n".join(x for x in pieces if x).strip()


def _parse_spamassassin(archive: Path, label: str) -> list[dict]:
    rows: list[dict] = []
    parser = BytesParser(policy=policy.default)
    with tarfile.open(archive, "r:bz2") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            name = Path(member.name).name.lower()
            if name in {"cmds", "readme", "readme.txt"}:
                continue
            handle = tf.extractfile(member)
            if not handle:
                continue
            raw = handle.read()
            try:
                msg = parser.parsebytes(raw)
                subject = str(msg.get("subject", "") or "").strip()
                body = _email_body(msg)
                text = f"Subject: {subject}\n{body}".strip()
            except Exception:
                text = _decode_bytes(raw)
            text = re.sub(r"\x00", " ", text).strip()
            if len(text) >= 8:
                rows.append({
                    "text": text[:50000],
                    "label": label,
                    "source": "Email",
                    "dataset": "SpamAssassin",
                })
    return rows


def _read_csv_from_zip(zf: zipfile.ZipFile, member_name: str) -> list[dict]:
    raw = zf.read(member_name)
    text = _decode_bytes(raw)
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        content = str(row.get("CONTENT", "") or "").strip()
        raw_class = str(row.get("CLASS", row.get("TAG", ""))).strip()
        if raw_class not in {"0", "1"} or not content:
            continue
        rows.append({
            "text": content[:50000],
            "label": "spam" if raw_class == "1" else "ham",
            "source": "Social Media",
            "dataset": "UCI YouTube Spam Collection",
        })
    return rows


def _parse_youtube(archive: Path) -> list[dict]:
    rows: list[dict] = []
    with zipfile.ZipFile(archive) as zf:
        csv_files = [n for n in zf.namelist() if n.lower().endswith(".csv") and "youtube" in n.lower()]
        if not csv_files:
            raise RuntimeError("UCI archive did not contain the expected YouTube CSV files")
        for name in sorted(csv_files):
            rows.extend(_read_csv_from_zip(zf, name))
    return rows


def _deduplicate(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key_text = re.sub(r"\s+", " ", row["text"].strip().lower())
        key = hashlib.sha256(key_text.encode("utf-8", errors="ignore")).digest()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def build_real_dataset(force_download: bool = False) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if force_download:
        for p in RAW_DIR.iterdir():
            if p.is_file():
                p.unlink()
        COMBINED.unlink(missing_ok=True)

    if COMBINED.exists() and COMBINED.stat().st_size > 10000:
        return COMBINED

    ham_file = _download(SPAMASSASSIN_HAM_URLS, RAW_DIR / "20030228_easy_ham.tar.bz2")
    spam_file = _download(SPAMASSASSIN_SPAM_URLS, RAW_DIR / "20030228_spam.tar.bz2")
    youtube_file = _download(YOUTUBE_URLS, RAW_DIR / "youtube_spam_collection.zip")

    rows = []
    rows.extend(_parse_spamassassin(ham_file, "ham"))
    rows.extend(_parse_spamassassin(spam_file, "spam"))
    rows.extend(_parse_youtube(youtube_file))
    rows = _deduplicate(rows)

    if len(rows) < 4000:
        raise RuntimeError(f"Real dataset build produced only {len(rows)} rows; expected at least 4,000")
    sources = {r["source"] for r in rows}
    if sources != {"Email", "Social Media"}:
        raise RuntimeError("Real dataset must contain both Email and Social Media rows")

    COMBINED.parent.mkdir(parents=True, exist_ok=True)
    with COMBINED.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "source", "dataset"])
        writer.writeheader()
        writer.writerows(rows)
    return COMBINED


def dataset_summary(path: Path = COMBINED) -> dict:
    counts = {
        "total": 0, "spam": 0, "ham": 0,
        "Email": {"spam": 0, "ham": 0},
        "Social Media": {"spam": 0, "ham": 0},
    }
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            label = row["label"].strip().lower()
            source = row["source"].strip()
            counts["total"] += 1
            counts[label] += 1
            if source in counts:
                counts[source][label] += 1
    return counts
