# JavascriptMusic

A personal music project combining AI generation, browser playback, and a taste engine that learns what you actually like.

## Vision

Generate music with Suno → rate it in a personal radio player → train a model on those ratings → use the model to auto-curate at scale → publish the best to Spotify/YouTube.

The taste is personal: jazz-influenced, complexity welcome, unexpected shifts are features not bugs. Generic lofi bot channels can't replicate that — this system learns *your* ear.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  GENERATION (overnight, M2 Mac)                     │
│  Suno API → batch generate N tracks                 │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  FEATURE EXTRACTION (taste-engine/extract.py)       │
│  librosa: BPM, key, energy, MFCC, spectral features │
│  → stored in SQLite with track metadata             │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  RADIO PLAYER  (radio-player/index.html)            │
│  Tone.js playback → you rate tracks 1-5             │
│  Borderline tracks (model uncertain) surface first  │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  TASTE MODEL  (taste-engine/model.py)               │
│  Trains on your ratings → scores new tracks         │
│  Active learning: auto-pass clear wins/fails,       │
│  queue uncertain tracks for human rating            │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  PUBLISH  (publish/)                                │
│  High-score tracks → YouTube API + DistroKid        │
│  FFmpeg stitches compilations for long-form uploads │
└─────────────────────────────────────────────────────┘
```

## Taste Profile

- Jazz-influenced: complex chord progressions, key changes, improvisation — all fine
- Craziness is a feature, not a bug
- Model learns the specific personal filter, not a genre average
- Active learning: only surfaces uncertain tracks for manual rating over time

## Stack

| Layer | Tool |
|-------|------|
| Generation | [gcui-art/suno-api](https://github.com/gcui-art/suno-api) (unofficial Suno wrapper) |
| Player | Tone.js (already in this repo) |
| Feature extraction | librosa (Python) |
| Taste model | sklearn (start simple: k-NN or weighted average, upgrade later) |
| Storage | SQLite |
| Batch jobs | Overnight runner on M2 Mac |
| Stitching | FFmpeg |
| Distribution | YouTube Data API v3 + DistroKid ($22/yr) |

## Economics

- Suno Premier: $30/mo → ~2,000 tracks/mo, commercial rights
- DistroKid: ~$2/mo → unlimited streaming distribution
- **Total: ~$35/mo**
- YouTube monetization: ~$1-3 CPM (lofi/ambient)
- Spotify: ~$0.003-0.005/stream
- Break-even timeline: 6-18 months depending on growth

## Directories

```
radio-player/   — browser UI, Tone.js playback + rating interface
taste-engine/   — Python: feature extraction, SQLite, taste model
generate/       — Suno API wrappers, batch generation scripts
publish/        — YouTube + DistroKid upload automation
legacy/         — original Tone.js hello world (2020)
```

## Original Experiment (2020)

First attempt: single Middle C via Tone.js following a Medium tutorial.
See `legacy/` — the seed of the idea.
