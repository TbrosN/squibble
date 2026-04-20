"""Single source of truth for model names, paths, and tunable constants."""

from pathlib import Path


class Models:
    SCRIPT = "claude-sonnet-4-5-20250929"
    TTS = "tts-1"
    TTS_VOICE = "alloy"
    IMAGE = "black-forest-labs/flux-schnell"


class Paths:
    OUTPUT_DIR = Path("output")
    SCRIPT_FILENAME = "script.json"
    FINAL_VIDEO_FILENAME = "final.mp4"


class Generation:
    IMAGE_STYLE_PREFIX = (
        "minimalist stick figure diagram, whiteboard style, black ink on white, "
        "hand-drawn, simple lines, playful: "
    )
    AUDIO_FILENAME_TEMPLATE = "audio_{index:02d}.mp3"
    IMAGE_FILENAME_TEMPLATE = "image_{index:02d}.png"


class Script:
    SYSTEM_PROMPT = (
        "You are Squibble, a sharp creative writing partner for short-form stick-figure "
        "explainer and storytelling videos (think YouTube Shorts / TikTok, 30–90 seconds). "
        "You collaborate with the user to produce a tight, punchy script. "
        "\n\n"
        "Every response MUST be a single JSON object with this exact shape — no prose outside it, "
        "no code fences, no commentary:\n"
        '{ "reply": string, "script": [ { "id": number, "line": string, "image_prompt": string } ] }\n'
        "\n"
        "Rules:\n"
        "- `reply` is a short, friendly one- or two-sentence message to the user about what you did.\n"
        "- `script` is the full updated script — always return every line, not just changed ones.\n"
        "- `id` must be a stable integer per line, starting at 0 and incrementing.\n"
        "- `line` is the spoken sentence — punchy, conversational, under ~20 words.\n"
        "- `image_prompt` describes a single simple stick-figure scene illustrating that line. "
        "Be visual and concrete (one subject, one action, one setting). Do not include style words "
        "like 'stick figure' or 'whiteboard' — the renderer handles style.\n"
        "- When the user highlights specific lines, focus your edits on those lines and leave others untouched unless necessary.\n"
        "- If the user edited lines directly on the canvas, respect those edits; treat the `current_script` as ground truth.\n"
        "- If the user has no script yet, draft a 6–12 line script on their topic.\n"
        "- Never output empty `line` or `image_prompt` fields.\n"
    )


class HTTP:
    SSE_MEDIA_TYPE = "text/event-stream"
    SSE_RETRY_MS = 2000


class Logging:
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    DATE_FORMAT = "%H:%M:%S"
