from pathlib import Path
import sqlite3
from contextlib import closing

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    cleaned_text TEXT NOT NULL,
    prediction TEXT NOT NULL,
    confidence REAL NOT NULL,
    spam_probability REAL NOT NULL,
    risk_level TEXT NOT NULL,
    signals TEXT NOT NULL,
    processing_ms REAL NOT NULL,
    model_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_prediction ON predictions(prediction);
CREATE INDEX IF NOT EXISTS idx_predictions_source ON predictions(source_type);
"""


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def init(self):
        with closing(self.connect()) as con:
            con.executescript(SCHEMA)
            con.commit()

    def add_prediction(self, record: dict) -> int:
        with closing(self.connect()) as con:
            cur = con.execute(
                """INSERT INTO predictions(
                    source_type,raw_text,cleaned_text,prediction,confidence,
                    spam_probability,risk_level,signals,processing_ms,model_version,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    record["source_type"], record["raw_text"], record["cleaned_text"],
                    record["prediction"], record["confidence"], record["spam_probability"],
                    record["risk_level"], ", ".join(record.get("signals", [])),
                    record["processing_ms"], record["model_version"], record["created_at"],
                ),
            )
            con.commit()
            return int(cur.lastrowid)

    def recent(self, limit: int = 8):
        with closing(self.connect()) as con:
            return con.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def search(self, query: str = "", label: str = "", source: str = "", limit: int = 250):
        sql = "SELECT * FROM predictions WHERE 1=1"
        params = []
        if query:
            sql += " AND raw_text LIKE ?"
            params.append(f"%{query}%")
        if label in {"Spam", "Not Spam"}:
            sql += " AND prediction=?"
            params.append(label)
        if source in {"Email", "Social Media", "API"}:
            sql += " AND source_type=?"
            params.append(source)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with closing(self.connect()) as con:
            return con.execute(sql, params).fetchall()

    def stats(self):
        with closing(self.connect()) as con:
            summary = con.execute("""
                SELECT COUNT(*) AS total,
                       COALESCE(SUM(CASE WHEN prediction='Spam' THEN 1 ELSE 0 END),0) AS spam,
                       COALESCE(SUM(CASE WHEN prediction='Not Spam' THEN 1 ELSE 0 END),0) AS ham,
                       COALESCE(AVG(processing_ms),0) AS avg_ms,
                       COALESCE(AVG(spam_probability),0) AS avg_spam_probability
                FROM predictions
            """).fetchone()
            by_source = con.execute("SELECT source_type,COUNT(*) AS count FROM predictions GROUP BY source_type ORDER BY count DESC").fetchall()
            by_risk = con.execute("SELECT risk_level,COUNT(*) AS count FROM predictions GROUP BY risk_level ORDER BY count DESC").fetchall()
            return {"summary": summary, "by_source": by_source, "by_risk": by_risk}

    def clear(self):
        with closing(self.connect()) as con:
            con.execute("DELETE FROM predictions")
            con.commit()
