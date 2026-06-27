#!/usr/bin/env python3
"""
Stitch high-scoring tracks into a long-form compilation for YouTube/streaming.

Requires: ffmpeg installed (brew install ffmpeg)

Usage:
  python3 stitch.py --duration 180  # build a 3-hour compilation
  python3 stitch.py --duration 60   # 1-hour
"""
import argparse
import sqlite3
import subprocess
import tempfile
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "taste-engine" / "taste.db"
OUTPUT_DIR = Path(__file__).parent.parent / "compilations"
AUTO_PASS_THRESHOLD = 0.75


def get_publish_queue(conn, target_minutes: int) -> list:
    rows = conn.execute(f"""
        SELECT path FROM tracks
        WHERE (model_score >= {AUTO_PASS_THRESHOLD} OR user_rating >= 4)
        AND published = 0
        ORDER BY model_score DESC, user_rating DESC
    """).fetchall()
    return [Path(r[0]) for r in rows if Path(r[0]).exists()]


def stitch(tracks: list, output: Path):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for t in tracks:
            f.write(f"file '{t.resolve()}'\n")
        list_path = f.name

    cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_path,
           "-c", "copy", str(output)]
    result = subprocess.run(cmd, capture_output=True)

    if result.returncode == 0:
        print(f"Compilation saved: {output}")
    else:
        print(f"FFmpeg error: {result.stderr.decode()}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=180, help="Target duration in minutes")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    tracks = get_publish_queue(conn, args.duration)

    if not tracks:
        print("No tracks in publish queue. Rate some tracks first.")
        return

    print(f"Found {len(tracks)} tracks in publish queue.")
    output = OUTPUT_DIR / f"compilation_{args.duration}min.mp3"
    stitch(tracks, output)
    conn.close()


if __name__ == "__main__":
    main()
