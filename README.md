# Squibble

An AI co-creative tool for generating narration-style YoutTube videos such as [this](https://www.youtube.com/shorts/uuYMYaa6sEQ?feature=share).

Write and refine a script alongside an agentic assistant, then watch it come to life as Squibble generates images and a voiceover, and stitches them together into a video.

```
squibble/
├── backend/    # FastAPI app — all LLM, TTS, image, and video logic
└── frontend/   # Next.js App Router — the liquid-glass studio UI
```

## Usage

1. **Script Studio.** Chat with the assistant at the bottom of the page,
   or edit the script manually. Click the line numbers to select them as context for the agent.
2. **Generation Studio.** Hit "Generate Video →". A grid of cards fills in
   top-to-bottom as each line's audio and image generate in parallel.
   Click a finished card to preview its image with audio. Cancel any time
   to go back to the script.
3. **Download.** When everything finishes, grab the stitched `.mp4`.

## Features I'm Proud Of
- Agent editing system: a file-backed script is edited using Anthropics built-in string replace-based editor tool.
  This resulted in a low-lift implementation that lets Claude use familiar tools from training, while also letting
  us support very long scripts natively, rather than carrying them in memory.
    - I designed a syntax for the script file, where line breaks are indicated by semicolons
    - System prompts for the image and script-writing agents are sufficiently informative about the overall process
    of the app and video format that they can make intelligent decisions about where to put line breaks and what kinds of images make sense to generate.

## Prerequisites

- Python 3.11+
- Node.js 20+
- `ffmpeg` on your `PATH` (used by the video assembly step)

## Backend

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
cd backend
uv sync
cp .env.example .env    # fill in your API keys
uv run main.py
```

The backend requires Claude, Gemini, and ElevenLabs API keys (see `.env.example`). You will need to fill these in if you want to run the app locally.

## Frontend

```bash
cd frontend
npm install
cp .env.example .env.local    # points at http://localhost:8000 by default
npm run dev
```

The only env var the frontend needs is `NEXT_PUBLIC_API_URL`. All LLM,
TTS, image, and video calls happen on the backend — the frontend bundle
holds no secrets.
