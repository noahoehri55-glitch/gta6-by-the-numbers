# GTA 6 by the Numbers

Faceless data channel: one long video plus Shorts per episode, built from public data. No Rockstar footage, trailers, screenshots or artwork.

## How it runs
1. **freeze** (`freeze.yml`): on a change to `episode.json`, pulls BLS (CPI-U, wages), Wikipedia pageviews and TTWO prices, then freezes them at `data_end` into `data/frozen/facts.json` (committed to `main`).
2. Scripts in `jobs/<name>/script.json` are written against that frozen file, so spoken and on-screen numbers match.
3. **render** (`render.yml`): on a change to `jobs/`, voices with ElevenLabs (per-beat cache), renders HTML scenes frame by frame, and pushes MP4s, captions, thumbnail and checks (frame sheets + loudness) to the `renders` branch.
4. **twitch-log** (`twitch.yml`): every 30 min, appends live Twitch viewers for GTA VI and GTA V to `twitch.csv` on the `data` branch (our own viewer history for launch week).
5. **voice-samples**: manual only, renders a sample with every premade voice to the `samples` branch.

Local layout test without credits: `TTS=silent python pipeline/voice.py <job>` then `python pipeline/render.py <job> preview 3 10 20`.

## Secrets / variables
- `ELEVENLABS_API_KEY` (secret), optional variable `ELEVENLABS_VOICE_ID` (e.g. own voice clone)
- `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET` (secrets)

## Disclosure
Narration is a synthetic voice. Background photos are AI-generated and show no real places. Tick "altered or synthetic content" on upload.
