# Squibble — Full-Stack MVP Spec (v3)

## Product Vision

A sleek two-stage creative tool: collaborate with AI to write a tight script, then watch it come to life as audio and images generate in real time. The experience feels like a professional creative studio.

---

## UI/UX Flow

### Stage 1 — Script Studio

A full-canvas **script editor** where each line is a directly editable block. A **chat bar** sits pinned at the bottom of the page — the user types naturally, and Claude responds by updating the script in place. Users can **highlight one or more lines** and send targeted feedback ("make this line funnier", "rewrite the intro") — selected lines are included in the request context automatically.

A **"Generate Video →"** CTA in the top-right advances to Stage 2.

### Stage 2 — Generation Studio

A **grid of cards**, one per script line. Each card shows:

- The image (placeholder shimmer → generated thumbnail)
- The line text beneath it
- An audio status indicator (pending / generating / ✓ done)

Clicking any card opens a **slide preview modal**: the image fills the modal and the audio plays over it — a lightweight per-slide preview without needing a full video player.

A persistent **"← Back to Script"** and a prominent red **"Cancel"** button are always visible. On cancel, the user returns to Stage 1 with the script intact.

Once all assets complete, a **"Download Video"** CTA appears.

---

## Design System

**Aesthetic:** Liquid glass — frosted translucent panels over a dark gradient, subtle blur, thin light borders.

```
Background:    #0a0a0f → #1a1a2e  (deep navy gradient)
Glass panels:  rgba(255,255,255,0.06), backdrop-filter: blur(20px)
               border: 1px solid rgba(255,255,255,0.12)
Accent:        #6366f1  (electric indigo)
Success:       #10b981  (soft emerald)
Cancel/danger: #f43f5e  (rose)
Text primary:  #f1f5f9
Text muted:    rgba(255,255,255,0.45)
```

Typography: Geist or Inter. Generous whitespace. No clutter.

---

## Project Structure

```
squibble/
├── frontend/          # Next.js app
└── backend/           # FastAPI app
```

---

## Frontend Architecture

**Stack:** Next.js (App Router), plain CSS modules with the glass design system. No component library — hand-styled.

All API keys and LLM calls live on the backend. The frontend only holds UI state and talks to the backend over a clean HTTP/SSE interface.

```
frontend/
├── .env.local                  # NEXT_PUBLIC_API_URL only — no secrets
├── .gitignore                  # includes .env.local
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx            # Stage router
│   │   └── globals.css         # Glass design tokens
│   ├── components/
│   │   ├── stage1/
│   │   │   ├── ScriptEditor.tsx    # Full-canvas editable line blocks
│   │   │   ├── LineBlock.tsx       # Single editable line, selectable
│   │   │   └── ChatBar.tsx         # Pinned bottom chat input
│   │   ├── stage2/
│   │   │   ├── GenerationGrid.tsx  # Responsive card grid
│   │   │   ├── SlideCard.tsx       # Image + line text + audio status
│   │   │   └── SlidePreviewModal.tsx  # Click-to-preview: image + audio
│   │   └── shared/
│   │       ├── GlassPanel.tsx
│   │       ├── ErrorMessage.tsx    # User-friendly error display
│   │       └── CancelButton.tsx
│   ├── hooks/
│   │   ├── useScriptEditor.ts  # Line CRUD, selection state
│   │   ├── useChat.ts          # Chat message state, POST to backend
│   │   └── useGeneration.ts    # SSE listener, cancel, asset state
│   ├── types/
│   │   └── index.ts            # ScriptLine, SlideAsset, ChatMessage, etc.
│   └── lib/
│       └── apiClient.ts        # Typed fetch wrapper (base URL from env)
```

The frontend **never** calls any LLM or media API directly. `apiClient.ts` points to `NEXT_PUBLIC_API_URL` — the only env var the frontend needs.

---

## Backend Architecture

**Stack:** Python + FastAPI, async throughout. All secrets in `.env` (gitignored). Business logic encapsulated in service classes.

```
backend/
├── .env                        # All API keys — never committed
├── .gitignore                  # includes .env
├── main.py                     # FastAPI app, mounts routers, CORS
├── constants.py                # Model names, paths, timing constants
├── config.py                   # Loads .env via pydantic-settings → Settings singleton
├── routers/
│   ├── script.py               # POST /script/chat
│   └── generation.py           # POST /generate/start
│                               # GET  /generate/stream/{job_id}
│                               # POST /generate/cancel/{job_id}
│                               # GET  /generate/asset/{job_id}/{filename}
│                               # GET  /generate/download/{job_id}
├── services/
│   ├── script_service.py       # ScriptService class — Claude chat, history mgmt
│   ├── audio_service.py        # AudioService class — TTS per line
│   ├── image_service.py        # ImageService class — image gen per line
│   ├── video_service.py        # VideoService class — ffmpeg assembly
│   └── generation_service.py   # GenerationService — orchestrates the above
├── models/
│   ├── script.py               # ScriptLine, ChatMessage Pydantic models
│   ├── job.py                  # Job, LineStatus, JobStatus models
│   └── events.py               # SSEEvent hierarchy
├── jobs/
│   └── store.py                # JobStore class — in-memory job registry
└── output/
    └── {job_id}/
        ├── script.json
        ├── audio_00.mp3 ...
        ├── image_00.png ...
        └── final.mp4
```

### Service Class Responsibilities

`**ScriptService**` — owns everything Claude-related for Stage 1. Maintains the system prompt, accepts the full message history from the router (passed in per request, since HTTP is stateless), and returns a structured `list[ScriptLine]` plus a reply string. No chat history is stored server-side — the frontend holds it and sends it each time.

`**AudioService**` — takes a `ScriptLine`, calls TTS, writes the `.mp3`, returns the file path and duration in seconds.

`**ImageService**` — takes a `ScriptLine`, calls the image API, writes the `.png`, returns the file path.

`**GenerationService**` — orchestrates `AudioService` and `ImageService` concurrently per line, checks the cancel event between lines, emits SSE events, calls `VideoService` when complete.

`**VideoService**` — wraps ffmpeg. Takes a list of `(image_path, audio_path, duration)` tuples and produces a `.mp4`.

`**JobStore**` — a singleton dict-backed registry of active `Job` objects. Provides `create()`, `get()`, `cancel()`.

---

## Data Models

```python
# models/script.py
class ScriptLine(BaseModel):
    id: int
    line: str
    image_prompt: str

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

# models/job.py
class LineGenerationStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    DONE = "done"
    ERROR = "error"

class LineStatus(BaseModel):
    id: int
    status: LineGenerationStatus
    image_url: str | None = None
    audio_url: str | None = None
    duration: float | None = None

class JobStatus(str, Enum):
    RUNNING = "running"
    CANCELLED = "cancelled"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class Job:
    id: str
    status: JobStatus
    lines: list[LineStatus]
    task: asyncio.Task
    cancel_event: asyncio.Event

# models/events.py
class SSEEventType(str, Enum):
    LINE_UPDATE = "line_update"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    ERROR = "error"

class SSEEvent(BaseModel):
    type: SSEEventType

class LineUpdateEvent(SSEEvent):
    type: SSEEventType = SSEEventType.LINE_UPDATE
    line_id: int
    status: LineGenerationStatus
    image_url: str | None = None
    audio_url: str | None = None
    duration: float | None = None

class CompleteEvent(SSEEvent):
    type: SSEEventType = SSEEventType.COMPLETE
    final_url: str

class CancelledEvent(SSEEvent):
    type: SSEEventType = SSEEventType.CANCELLED

class ErrorEvent(SSEEvent):
    type: SSEEventType = SSEEventType.ERROR
    line_id: int
    message: str
```

The `emit()` helper calls `.model_dump_json()` on any `SSEEvent` subclass — so every event is validated, typed, and serialized consistently with no raw dicts anywhere in the generation pipeline.

---

## API Contract

### Stage 1

```
POST /script/chat
Body: {
  messages: ChatMessage[],       // full history — frontend owns this
  selected_lines: int[],         // IDs of highlighted lines (may be empty)
  current_script: ScriptLine[]   // current canvas state (direct edits included)
}
Response: {
  reply: string,
  script: ScriptLine[]           // full updated script for canvas re-render
}
```

The backend always returns the **complete updated script** — the frontend replaces its canvas state wholesale. This means direct edits made on the canvas are sent up with each chat message, so Claude always has the latest version.

### Stage 2

```
POST /generate/start
Body: { script: ScriptLine[] }
Response: { job_id: string }

GET /generate/stream/{job_id}         ← Server-Sent Events
Events:
  LineUpdateEvent  — per-line status, image_url, audio_url, duration
  CompleteEvent    — final_url for download
  CancelledEvent   — generation halted by user
  ErrorEvent       — line_id + user-friendly message

POST /generate/cancel/{job_id}
Response: { ok: true }

GET /generate/asset/{job_id}/{filename}   ← serves image/audio files
GET /generate/download/{job_id}           ← streams final.mp4
```

Asset URLs in SSE events are relative paths that resolve through `/generate/asset/...` — the backend is the sole file server. The frontend never needs direct filesystem access.

---

## Generation Orchestration

```python
# Inside GenerationService.run()
for line in script:
    if cancel_event.is_set():
        emit(CancelledEvent())
        break

    emit(LineUpdateEvent(line_id=line.id, status=LineGenerationStatus.GENERATING))

    audio_result, image_result = await asyncio.gather(
        audio_service.generate(line, job_dir),
        image_service.generate(line, job_dir),
    )

    emit(LineUpdateEvent(
        line_id=line.id,
        status=LineGenerationStatus.DONE,
        image_url=image_result.url,
        audio_url=audio_result.url,
        duration=audio_result.duration,
    ))

final = await video_service.assemble(completed_lines, job_dir)
emit(CompleteEvent(final_url=final.url))
```

Audio and image generation run **concurrently per line**. Lines are processed **sequentially** so the grid fills top-to-bottom naturally and cancellation halts at a clean boundary.

---

## Cancellation Flow

1. User clicks Cancel
2. Frontend POSTs to `/generate/cancel/{job_id}`
3. Backend sets `job.cancel_event` → generation loop exits at next line boundary
4. SSE emits `CancelledEvent`
5. Frontend receives it → returns user to Stage 1 with script state intact (held in frontend state the whole time)

---

## Constants & Config Pattern

```python
# constants.py — single source of truth, no magic strings
class Models:
    SCRIPT = "claude-sonnet-4-5"
    TTS = "tts-1"
    IMAGE = "flux-schnell"

class Paths:
    OUTPUT_DIR = Path("output")

class Generation:
    IMAGE_STYLE_PREFIX = "minimalist stick figure diagram, whiteboard style: "
    MAX_CONCURRENT_LINES = 1   # sequential for now; easy to increase

# config.py — typed settings from .env
class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    replicate_api_token: str
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

## Style Guidelines

> This section is the authoritative reference for code style decisions across the Squibble codebase.

**Modularity.** Each file has a single clear responsibility. Organize by ownership — routers handle HTTP concerns only, services own business logic, models own data shapes. If a file is doing two distinct things, split it.

**No magic values.** All model names, file paths, style prefixes, timing constants, and string literals belong in `constants.py`. No hardcoded strings scattered through service or router code.

**Dead code policy.** If a function, class, or file is created during development and ends up unused, delete it before committing. The codebase should reflect what the system actually does.

**OOP over raw dicts.** Any structured data — script lines, job state, SSE events, service results — must be a Pydantic model or dataclass. Raw `dict` passing between functions or layers is not acceptable. This includes SSE event emission: call `.model_dump_json()` on a typed event object, never construct `{"type": "..."}` inline.

**Secrets stay on the backend.** API keys and credentials live in `backend/.env` (gitignored) and are loaded via the `Settings` pydantic-settings class. The frontend `.env.local` may only contain `NEXT_PUBLIC_API_URL`. Nothing sensitive ever touches the frontend bundle.

**Frontend/backend boundary.** The frontend is responsible for UI state and user interaction only. All LLM calls, prompt construction, chat history management, system prompts, and file handling are backend concerns. The frontend sends user intent; the backend decides how to fulfill it.

**Frontend Custom Component Library.** For repeated styles used throughout the site, do not rewrite similar code across components. Instead, create custom component primitives for our project, such as Button.tsx that can be reused across many components.

---

## Error Handling & Logging

**Severity levels.** Use `logger.error` for fatal errors that result in broken functionality (generation failed, ffmpeg crashed, API key invalid). Use `logger.warning` for non-fatal errors (one line failed but others can continue). All logs must reach the terminal running the backend process — use Python's standard `logging` module configured at app startup in `main.py`, not `print`.

**Call stack pattern.** Only top-level functions (routers and the top of `GenerationService.run()`) log warnings or errors. All other functions simply re-raise with their own context appended:

```python
# Deep function — re-raise only
async def generate(self, line: ScriptLine, job_dir: Path) -> AudioResult:
    try:
        ...
    except Exception as e:
        raise RuntimeError(f"AudioService failed on line {line.id}: {e}") from e

# Top-level — log once, with full context
async def run(self):
    try:
        ...
    except Exception as e:
        logger.error(f"Generation job {self.job_id} failed: {e}")
        emit(ErrorEvent(line_id=current_line_id, message="Something went wrong generating this slide."))
```

This ensures no duplicate log entries and that the full call stack context is preserved in a single log line.

**User-facing errors.** Users never see raw exception messages. The frontend's `ErrorMessage` component displays a clean, readable message passed from the backend. SSE `ErrorEvent` carries a friendly `message` field — not the internal exception string. HTTP error responses from routers use a consistent `{ "error": "<friendly message>" }` shape. The frontend must always handle error states gracefully without breaking layout or leaving the user stuck.

---

## Security & Secrets


| Location              | What lives there                                          |
| --------------------- | --------------------------------------------------------- |
| `backend/.env`        | All API keys — gitignored                                 |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` only — no secrets                   |
| Frontend bundle       | Nothing sensitive — all LLM calls proxied through backend |


---

## Out of Scope for MVP

- Auth / user accounts
- Persisted project history
- Caption burn-in
- Background music
- Social media upload
- Per-line retry on failure

