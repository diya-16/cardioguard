"""
db.py
SQLite wrapper — saves predictions, fetches history, computes trends.
Auto-creates the database and table on first use.

FIXES:
  - BUG: `dict | None` return type hint uses Python 3.10+ syntax.
    On Python 3.9 (which many users run) this raises a TypeError at import time.
    FIX: use `Optional[dict]` from typing instead.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "history.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp      TEXT    NOT NULL,
                user_name      TEXT    DEFAULT 'User',
                age            REAL,
                gender         INTEGER,
                height         REAL,
                weight         REAL,
                ap_hi          INTEGER,
                ap_lo          INTEGER,
                cholesterol    INTEGER,
                gluc           INTEGER,
                smoke          INTEGER,
                alco           INTEGER,
                active         INTEGER,
                bmi            REAL,
                pulse_pressure REAL,
                map            REAL,
                hypertension   INTEGER,
                obese          INTEGER,
                risk_score     REAL,
                risk_label     TEXT,
                probability    REAL,
                contributions  TEXT,
                flagged        TEXT
            )
        """)
        conn.commit()


def save_prediction(result: dict, raw: dict, user_name: str = 'User') -> None:
    """
    Save a prediction result to the database.

    Parameters
    ----------
    result    : dict returned by predictor.predict()
    raw       : dict of raw user inputs
    user_name : str display name for the session
    """
    init_db()
    eng = result['engineered']
    with _connect() as conn:
        conn.execute("""
            INSERT INTO predictions (
                timestamp, user_name,
                age, gender, height, weight, ap_hi, ap_lo,
                cholesterol, gluc, smoke, alco, active,
                bmi, pulse_pressure, map, hypertension, obese,
                risk_score, risk_label, probability,
                contributions, flagged
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        """, (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_name,
            eng['age'], eng['gender'], eng['height'], eng['weight'],
            eng['ap_hi'], eng['ap_lo'],
            eng['cholesterol'], eng['gluc'],
            eng['smoke'], eng['alco'], eng['active'],
            eng['bmi'], eng['pulse_pressure'], eng['map'],
            eng['hypertension'], eng['obese'],
            result['risk_score'], result['risk_label'], result['probability'],
            json.dumps(result['contributions']),
            json.dumps(result['flagged']),
        ))
        conn.commit()


def get_history(user_name: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
    """
    Fetch prediction history as a DataFrame.
    If user_name is given, filters to that user.
    """
    init_db()
    with _connect() as conn:
        if user_name:
            rows = conn.execute(
                "SELECT * FROM predictions WHERE user_name = ? ORDER BY timestamp DESC LIMIT ?",
                (user_name, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM predictions ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([dict(r) for r in rows])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def get_trend_data(user_name: Optional[str] = None) -> pd.DataFrame:
    """
    Returns a time-series DataFrame for plotting trends.
    """
    df = get_history(user_name=user_name)
    if df.empty:
        return df

    trend_cols = ['timestamp', 'risk_score', 'ap_hi', 'ap_lo',
                  'bmi', 'weight', 'pulse_pressure', 'map', 'risk_label']
    available = [c for c in trend_cols if c in df.columns]
    return df[available].sort_values('timestamp')


def get_latest(user_name: Optional[str] = None) -> Optional[dict]:  # ✅ FIX: was `dict | None`
    """
    Returns the most recent prediction as a dict, or None if no history.
    """
    df = get_history(user_name=user_name, limit=1)
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    row['contributions'] = json.loads(row.get('contributions') or '[]')
    row['flagged']       = json.loads(row.get('flagged') or '[]')
    return row


def get_stats(user_name: Optional[str] = None) -> dict:
    """Returns summary stats for the history panel."""
    df = get_history(user_name=user_name)
    if df.empty:
        return {
            'total_checks': 0,
            'avg_risk':     None,
            'trend':        None,
            'last_check':   None,
        }

    total = len(df)
    avg   = round(df['risk_score'].mean(), 1)
    last  = df.iloc[0]['timestamp'].strftime('%d %b %Y')

    if total >= 4:
        mid  = total // 2
        old  = df.iloc[mid:]['risk_score'].mean()
        new  = df.iloc[:mid]['risk_score'].mean()
        diff = new - old
        trend = 'worsening' if diff > 2 else ('improving' if diff < -2 else 'stable')
    else:
        trend = 'not enough data'

    return {
        'total_checks': total,
        'avg_risk':     avg,
        'trend':        trend,
        'last_check':   last,
    }


def delete_history(user_name: Optional[str] = None) -> None:
    """Delete all records for a user (or all records if no user given)."""
    init_db()
    with _connect() as conn:
        if user_name:
            conn.execute("DELETE FROM predictions WHERE user_name = ?", (user_name,))
        else:
            conn.execute("DELETE FROM predictions")
        conn.commit()
