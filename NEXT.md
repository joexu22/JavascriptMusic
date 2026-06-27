# Next Steps

## Status: Skeleton complete, not yet wired up

All the pieces exist but nothing talks to each other yet. No Suno connection, no live backend, no ratings database.

## To activate (in order)

### 1. Suno API (the music source)
```bash
git clone https://github.com/gcui-art/suno-api
cd suno-api
# add your Suno session cookie to .env
docker-compose up -d
# now running on localhost:3000
```
Then test: `python3 generate/suno.py --prompt "jazz lofi piano" --count 3`

### 2. Feature extraction
```bash
pip install librosa scikit-learn numpy
python3 taste-engine/extract.py --batch tracks/
# populates taste.db with audio features
```

### 3. Backend server for the radio player
Radio player (`radio-player/index.html`) expects a REST API:
- `GET /api/next` — next track to rate (uncertain ones first)
- `POST /api/rate` — save rating `{ id, rating }`
- `GET /api/queue/stats` — counts

**This server doesn't exist yet** — needs to be written. Flask or FastAPI, ~50 lines, talks to taste.db.

### 4. Train the taste model
Need at least 5-10 rated tracks before training is useful:
```bash
python3 taste-engine/model.py train
```
After that, model auto-scores new incoming tracks.

### 5. Stitch and publish
Once publish queue has enough tracks:
```bash
python3 publish/stitch.py --duration 180
# → compilations/compilation_180min.mp3
```
Then upload manually or wire YouTube Data API v3.

---

## Bigger decisions still open

- **Visual identity**: What does the channel look like? Need a consistent thumbnail style. (Lox can do this — connect to the existing SeaArt pipeline)
- **Channel name / brand**: Needs a name before going public
- **Distribution**: DistroKid signup ($22/yr) for Spotify/Apple Music
- **YouTube channel**: Create dedicated channel, not the main one

## The loop once running

```
overnight: generate/suno.py --batch
morning:   extract.py --batch tracks/
           model.py train
           open radio-player in browser, rate 10-15 tracks
           model.py score
           check publish queue
weekend:   stitch.py + upload
```

## Economics reminder
- Suno Premier: $30/mo → ~2,000 tracks/mo
- DistroKid: $22/yr
- Break-even: 6-18 months on YouTube, faster on Spotify if playlisted
