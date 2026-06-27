#!/usr/bin/env python3
"""
Taste model: trains on user ratings, scores new tracks, flags uncertain ones.

Strategy:
  - Start with weighted k-NN on audio features (BPM, energy, MFCC)
  - Active learning: tracks where model is uncertain (score near 0.5)
    get surfaced to the user first
  - Auto-pass: score > 0.75 → publish queue
  - Auto-fail: score < 0.25 → discard
  - Borderline: 0.25-0.75 → surface for human rating

Usage:
  python3 model.py train       # retrain on all rated tracks
  python3 model.py score       # score all unscored tracks
  python3 model.py stats       # show queue stats
"""
import ast
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "taste.db"

AUTO_PASS_THRESHOLD = 0.75
AUTO_FAIL_THRESHOLD = 0.25


def get_rated_tracks(conn):
    rows = conn.execute("""
        SELECT bpm, energy, mfcc, user_rating
        FROM tracks
        WHERE user_rating IS NOT NULL
    """).fetchall()
    return rows


def build_features(bpm, energy, mfcc_str):
    mfcc = ast.literal_eval(mfcc_str)
    return [bpm / 200.0, energy * 10] + [m / 100.0 for m in mfcc]


def train(conn):
    rows = get_rated_tracks(conn)
    if len(rows) < 5:
        print(f"Need at least 5 rated tracks to train. Have {len(rows)}.")
        return None

    try:
        from sklearn.neighbors import KNeighborsClassifier
        import numpy as np
    except ImportError:
        print("Run: pip install scikit-learn numpy")
        return None

    X = [build_features(r[0], r[1], r[2]) for r in rows]
    # Binarize: rating >= 4 = good (1), <= 2 = bad (0), 3 = skip
    y = [1 if r[3] >= 4 else 0 for r in rows if r[3] != 3]
    X = [x for x, r in zip(X, rows) if r[3] != 3]

    model = KNeighborsClassifier(n_neighbors=min(5, len(X)))
    model.fit(X, y)
    print(f"Trained on {len(X)} tracks.")
    return model


def score_all(conn, model):
    rows = conn.execute("""
        SELECT id, bpm, energy, mfcc FROM tracks
        WHERE model_score IS NULL AND bpm IS NOT NULL
    """).fetchall()

    for row in rows:
        id_, bpm, energy, mfcc_str = row
        features = [build_features(bpm, energy, mfcc_str)]
        try:
            prob = model.predict_proba(features)[0][1]
        except Exception:
            prob = 0.5
        conn.execute("UPDATE tracks SET model_score = ? WHERE id = ?", (prob, id_))

    conn.commit()
    print(f"Scored {len(rows)} tracks.")


def stats(conn):
    total = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
    rated = conn.execute("SELECT COUNT(*) FROM tracks WHERE user_rating IS NOT NULL").fetchone()[0]
    auto_pass = conn.execute(f"SELECT COUNT(*) FROM tracks WHERE model_score >= {AUTO_PASS_THRESHOLD}").fetchone()[0]
    uncertain = conn.execute(f"SELECT COUNT(*) FROM tracks WHERE model_score BETWEEN {AUTO_FAIL_THRESHOLD} AND {AUTO_PASS_THRESHOLD}").fetchone()[0]
    published = conn.execute("SELECT COUNT(*) FROM tracks WHERE published = 1").fetchone()[0]

    print(f"""
Taste Engine Stats
──────────────────
Total tracks:    {total}
Rated by you:    {rated}
Auto-pass queue: {auto_pass}
Needs your ear:  {uncertain}
Published:       {published}
    """)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    conn = sqlite3.connect(DB_PATH)

    if cmd == "train":
        model = train(conn)
        if model:
            score_all(conn, model)
    elif cmd == "score":
        model = train(conn)
        if model:
            score_all(conn, model)
    elif cmd == "stats":
        stats(conn)
    else:
        print("Usage: model.py [train|score|stats]")

    conn.close()


if __name__ == "__main__":
    main()
