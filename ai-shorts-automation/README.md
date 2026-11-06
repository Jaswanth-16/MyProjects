# AI Shorts Automation — upgraded foundation

A free-first, review-first vertical video builder adapted from the existing [AI-Shorts-Automation](https://github.com/Jaswanth-16/AI-Shorts-Automation) prototype.

## What's new
- Scene-level narration, so visual durations follow actual voice lengths (instead of a single narration track that may drift).
- Per-scene image inputs, 9:16 crops, gentle animated camera movement, burned-in readable captions, and a story JSON schema with visual prompts.
- Optional Edge TTS voices (internet required) with offline espeak-ng fallback. Language/voice support depends on the chosen provider.
- Deterministic local smoke tests, validation, and artifact output.
- Private YouTube upload script (opt-in, credentials required); **never automatically publishes**.

## Quick start
Install Python 3.11+, FFmpeg and espeak-ng. From this directory:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python pipeline.py --story story.json --output output --voice offline
```

Output: `output/short.mp4`. Replace `images/scene_01.png` etc. with your own artwork. If missing, clear labeled placeholder artwork is generated; **this is not AI image generation**. The `visual_prompt` field is a handoff for a separately configured image generator.

For optional natural neural narration, install `edge-tts` and run:

```bash
python -m pip install edge-tts
python pipeline.py --voice edge --edge-voice en-US-AriaNeural
```

Edge TTS is a network-dependent service and may fail or be rate-limited; no silent fallback is performed. Select a voice appropriate to the script language.

## Private YouTube review
Install `google-api-python-client google-auth-oauthlib google-auth-httplib2`, obtain an OAuth desktop client JSON from Google Cloud with YouTube Data API enabled, and run:

```bash
python upload_private.py --video output/short.mp4 --client-secret client_secret.json --title "My Short"
```

This opens OAuth authorization and uploads with `privacyStatus=private`. The script never makes videos public. Never commit client secrets or token files.

## Limits and verification
- Local CPU video assembly; no promise of high-quality generative motion or GPU AI rendering.
- A source image per scene improves quality substantially. Placeholder cards are intentionally basic.
- Unit tests cover schema and duration constraints. Rendering and YouTube upload need separate integration checks.
- Use only artwork, narration and music you have rights to. Review generated content before publication.
