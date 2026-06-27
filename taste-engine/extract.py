#!/usr/bin/env python3
"""
Feature extraction for the taste engine.
Pulls audio features from a track file using librosa and stores in SQLite.

Usage:
  python3 extract.py path/to/track.mp3
  python3 extract.py --batch path/to/tracks/
"""
import argparse
import sqlite3
from pathlib import Path

# pip install librosa
try:
    import librosa
    import numpy as np
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    print("librosa not installed. Run: pip install librosa")

DB_PATH = Path(__file__).parent / "taste.db"


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id          INTEGER PRIMARY KEY,
            path        TEXT UNIQUE,
            title       TEXT,
            bpm         REAL,
            key         TEXT,
            energy      REAL,
            danceability REAL,
            valence     REAL,
            mfcc        TEXT,   -- JSON array of 13 MFCC means
            user_rating INTEGER DEFAULT NULL,
            model_score REAL    DEFAULT NULL,
            published   INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


def extract_features(path: Path) -> dict:
    y, sr = librosa.load(path, duration=60)  # sample first 60s for speed

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_idx = chroma.mean(axis=1).argmax()
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    rms = librosa.feature.rms(y=y).mean()
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1).tolist()

    return {
        "bpm": float(tempo),
        "key": keys[key_idx],
        "energy": float(rms),
        "mfcc": str(mfcc),
    }


def ingest(path: Path, conn):
    if not HAS_LIBROSA:
        print("librosa required for feature extraction")
        return

    features = extract_features(path)
    conn.execute("""
        INSERT OR IGNORE INTO tracks (path, title, bpm, key, energy, mfcc)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (str(path), path.stem, features["bpm"], features["key"],
          features["energy"], features["mfcc"]))
    conn.commit()
    print(f"Ingested: {path.name} | BPM: {features['bpm']:.1f} | Key: {features['key']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Audio file or directory (with --batch)")
    parser.add_argument("--batch", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    p = Path(args.path)
    if args.batch:
        files = list(p.glob("*.mp3")) + list(p.glob("*.wav")) + list(p.glob("*.webm"))
        for f in sorted(files):
            ingest(f, conn)
    else:
        ingest(p, conn)

    conn.close()


if __name__ == "__main__":
    main()
