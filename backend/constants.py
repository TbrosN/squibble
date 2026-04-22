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
    SCRIPT_FILENAME = "script.json"        # Stage 2 per-job frozen script snapshot
    CHAT_SCRIPT_FILENAME = "script.txt"    # Stage 1 live chat buffer (tool target)
    FINAL_VIDEO_FILENAME = "final.mp4"


class Generation:
    IMAGE_STYLE_PREFIX = (
        "minimalist stick figure diagram, whiteboard style, black ink on white, "
        "hand-drawn, simple lines, playful. Illustrate the core idea of this line "
        "as a single concrete scene: "
    )
    AUDIO_FILENAME_TEMPLATE = "audio_{index:02d}.mp3"
    IMAGE_FILENAME_TEMPLATE = "image_{index:02d}.png"


class Script:
    # Path the model uses to refer to the script buffer via the text editor tool.
    # The buffer lives in memory on the server; this is just a stable identifier
    # the tool expects.
    BUFFER_PATH = "/script.txt"

    # Line terminator in the buffer. Every spoken line ends with this character;
    # parsing the buffer into ScriptLine[] is just `split(LINE_TERMINATOR)` +
    # strip + filter empties.
    LINE_TERMINATOR = ";"

    # Upper bound on text-editor tool-use iterations per chat turn, to cap runaway
    # tool loops. 8 is generous for any realistic edit session.
    MAX_TOOL_ITERATIONS = 8

    # Anthropic text editor tool descriptor. For Claude 4.x models (including
    # Sonnet 4.6) the current version is text_editor_20250728, which exposes
    # view / create / str_replace / insert commands. No beta header required.
    TEXT_EDITOR_TOOL = {
        "type": "text_editor_20250728",
        "name": "str_replace_based_edit_tool",
    }

    SYSTEM_PROMPT = (
        "You are Squibble, a sharp creative writing partner for short-form "
        "stick-figure explainer and storytelling videos (think YouTube Shorts / "
        "TikTok, 30–90 seconds). You collaborate with the user to produce a "
        "tight, punchy script.\n"
        "\n"
        "You edit a single plain-text file at `/script.txt` using the text "
        "editor tool. The file is the full spoken script. Each spoken line is a "
        "single physical line ending with a semicolon (`;`). That's the only "
        "syntax.\n"
        "\n"
        "Example file contents:\n"
        "Most people think procrastination is laziness;\n"
        "But it's actually a feedback loop with your own anxiety;\n"
        "Here's how to break it;\n"
        "\n"
        "Editing rules:\n"
        "- If `/script.txt` is empty, use `create` to write a full initial "
        "script of 6–12 lines on the user's topic. Each line ends with `;` and "
        "sits on its own physical line.\n"
        "- To change or extend an existing script, use `str_replace` or "
        "`insert` to make the smallest useful edit. Never rewrite the whole "
        "file when a targeted edit will do.\n"
        "- Before a non-trivial edit, `view` the file to see its current state "
        "— the user may have edited it directly on the canvas between turns.\n"
        "- When the user has selected specific lines, focus your edits on those "
        "and leave the rest untouched unless the user asks otherwise.\n"
        "- If your `str_replace` target text appears more than once in the "
        "file, extend the match with a neighboring line so it becomes unique.\n"
        "\n"
        "Writing rules:\n"
        "- Each line is a single spoken sentence — punchy, conversational, "
        "under ~20 words.\n"
        "- Never use `;` as English punctuation inside a line. Use commas, em "
        "dashes, or split it into two lines.\n"
        "- Keep lines self-contained enough that an illustrator could draw one "
        "simple scene from each.\n"
        "\n"
        "After you finish editing, reply to the user with a short one- or "
        "two-sentence message about what you changed. Do not paste the script "
        "into your reply — the canvas already shows it.\n"
    )


class HTTP:
    SSE_MEDIA_TYPE = "text/event-stream"
    SSE_RETRY_MS = 2000


class Logging:
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    DATE_FORMAT = "%H:%M:%S"
