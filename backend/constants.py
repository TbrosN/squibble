"""Single source of truth for model names, paths, and tunable constants."""

from pathlib import Path


class Models:
    SCRIPT = "claude-sonnet-4-6" # same price as sonnet 4.5, but better
    TTS = "eleven_flash_v2_5"
    TTS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
    TTS_OUTPUT_FORMAT = "mp3_44100_128"
    IMAGE = "gemini-2.5-flash-image"


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
        "You are an expert storyteller who makes YouTube videos watched by millions.",
        "Each line of your scripts is clear and short (~<10 words);",
        "every line fights for its life and has no wasted words.",
    )


class HTTP:
    SSE_MEDIA_TYPE = "text/event-stream"
    SSE_RETRY_MS = 2000


class Logging:
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    DATE_FORMAT = "%H:%M:%S"
