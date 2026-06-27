#!/usr/bin/env python3
"""
Suno batch generation wrapper.
Uses gcui-art/suno-api (self-hosted, reverse-engineered).

Setup:
  git clone https://github.com/gcui-art/suno-api
  cd suno-api && docker-compose up -d
  (runs on localhost:3000 by default)

Usage:
  python3 suno.py --prompt "jazzy lofi with piano, complex chords, late night vibes" --count 10
  python3 suno.py --batch   # runs overnight prompts from prompts.txt
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

SUNO_API = "http://localhost:3000"
OUTPUT_DIR = Path(__file__).parent.parent / "tracks"

# Jazz-friendly prompt templates — complexity and weirdness welcome
JAZZ_PROMPTS = [
    "late night jazz lofi, complex piano chords, brushed drums, walking bass, warm vinyl crackle",
    "modal jazz lofi, Miles Davis influenced, muted trumpet, rhodes piano, slow and smoky",
    "bossa nova lofi, nylon string guitar, soft samba rhythm, dreamy and melancholic",
    "bebop lofi, fast chord changes, upright bass, brushed snare, coffee shop at 2am",
    "fusion jazz lofi, fender rhodes, electric bass, unexpected key modulations, cinematic",
    "free jazz ambient, abstract piano, sparse percussion, tension and release, deep night",
    "jazz ballad lofi, slow tempo, lush chords, single saxophone, rain on the window",
    "hard bop lofi, aggressive piano comping, walking bass, straight-ahead swing, focused energy",
]


def generate(prompt: str, count: int = 1) -> list:
    payload = json.dumps({
        "prompt": prompt,
        "make_instrumental": True,
        "wait_audio": True,
    }).encode()

    req = urllib.request.Request(
        f"{SUNO_API}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"[suno] Generation failed: {e}")
        return []


def download(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"[suno] Download failed: {e}")
        return False


def batch_generate(prompts: list, per_prompt: int = 3):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0

    for prompt in prompts:
        print(f"\nPrompt: {prompt[:60]}...")
        results = generate(prompt, per_prompt)

        for track in results:
            title = track.get("title", f"track_{int(time.time())}")
            audio_url = track.get("audio_url")
            if not audio_url:
                continue

            safe_title = "".join(c if c.isalnum() or c in "-_ " else "" for c in title)[:50]
            dest = OUTPUT_DIR / f"{int(time.time())}_{safe_title}.mp3"
            if download(audio_url, dest):
                print(f"  Saved: {dest.name}")
                total += 1

        time.sleep(5)

    print(f"\nBatch done. {total} tracks saved to {OUTPUT_DIR}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="Single prompt")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--batch", action="store_true", help="Run all jazz prompts")
    args = parser.parse_args()

    if args.batch:
        batch_generate(JAZZ_PROMPTS, per_prompt=args.count)
    elif args.prompt:
        batch_generate([args.prompt], per_prompt=args.count)
    else:
        print("Use --prompt or --batch")


if __name__ == "__main__":
    main()
