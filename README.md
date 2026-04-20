# Squibble

A sleek two-stage creative tool: collaborate with AI to write a tight script,
then watch it come to life as audio and images generate in real time.

```
squibble/
├── backend/    # FastAPI app — all LLM, TTS, image, and video logic
└── frontend/   # Next.js App Router — the liquid-glass studio UI
```

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
uv run uvicorn main:app --reload --port 8000
```

`uv sync` creates `.venv/` and installs locked dependencies from `uv.lock`.
To work inside the venv manually: `source .venv/bin/activate` then run
`uvicorn` as usual.

Required env vars (in `backend/.env`, never committed):

| Key                   | Purpose                              |
| --------------------- | ------------------------------------ |
| `ANTHROPIC_API_KEY`   | Claude — script writing (Stage 1)    |
| `OPENAI_API_KEY`      | `tts-1` — per-line audio             |
| `REPLICATE_API_TOKEN` | `flux-schnell` — per-line image      |
| `CORS_ALLOW_ORIGINS`  | Comma-sep origin list (default `http://localhost:3000`) |

Generated media lives under `backend/output/{job_id}/` and is served back
through `/generate/asset/...` and `/generate/download/...`.

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

## Flow

1. **Script Studio.** Chat with the assistant at the bottom of the page.
   Every line is directly editable. Click any line's number to include it
   in your next request ("make this one funnier").
2. **Generation Studio.** Hit "Generate Video →". A grid of cards fills in
   top-to-bottom as each line's audio and image generate in parallel.
   Click a finished card to preview its image with audio. Cancel any time
   to go back to the script.
3. **Download.** When everything finishes, grab the stitched `.mp4`.

## Project conventions

See [`SPEC.md`](./SPEC.md) for the full style guide. Highlights:

- All model names, paths, and style prefixes live in `backend/constants.py`.
- Every structured value crossing a function boundary is a Pydantic model or
  `@dataclass` — no raw `dict` passing.
- Secrets only exist in `backend/.env`. Frontend `.env.local` may only contain
  `NEXT_PUBLIC_API_URL`.
- Top-level routers / orchestrators are the only places that `logger.error` /
  `logger.warning`. Deep helpers re-raise with added context.
