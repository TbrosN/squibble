"""Single source of truth for model names, paths, and tunable constants."""

from pathlib import Path


class Models:
    SCRIPT = "claude-sonnet-4-6" # same price as sonnet 4.5, but better
    TTS = "eleven_flash_v2_5"
    TTS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
    TTS_OUTPUT_FORMAT = "mp3_44100_128"
    GOOGLE_TTS_LANGUAGE_CODE = "en-US"
    GOOGLE_TTS_VOICE_NAME = "en-US-Chirp3-HD-Algenib"
    GOOGLE_TTS_AUDIO_ENCODING = "MP3"
    IMAGE = "gemini-2.5-flash-image"


class Paths:
    OUTPUT_DIR = Path("output")
    SCRIPT_FILENAME = "script.json"        # Stage 2 per-job frozen script snapshot
    CHAT_SCRIPT_FILENAME = "script.txt"    # Stage 1 live chat buffer (tool target)
    FINAL_VIDEO_FILENAME = "final.mp4"


class Generation:
    IMAGE_STYLE_PREFIX = (
        "Simple hand-drawn illustration, playful and friendly, bold clean lines, "
        "flat colors with a white paper background. You can use stick figures, icons, and/or arrows if needed."
        "Use color freely, but keep the palette limited and cohesive."
        "Avoid text, letters, numbers, words, captions, or labels."
        "Keep the image extremely simple and instantly parseable — this image is only on screen "
        "for a couple of seconds, so one clear focal idea beats a busy scene. "
        "The image will be shown over the following spoken line: "
    )
    AUDIO_FILENAME_TEMPLATE = "audio_{index:02d}.mp3"
    IMAGE_FILENAME_TEMPLATE = "image_{index:02d}.png"

    # TikTok / Shorts vertical format. The image model supports a fixed set of
    # aspect-ratio strings; the rendered video is then padded/scaled to this
    # exact pixel resolution so every segment matches.
    IMAGE_ASPECT_RATIO = "9:16"
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920


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
        "illustrated explainer and storytelling videos (think YouTube Shorts / "
        "TikTok, 30-90 seconds). You collaborate with the user to produce a "
        "tight script that reads like a story.\n"
        "\n"
        "Personality: witty, a little sarcastic, warm, and relatable. You "
        "write the way a clever friend talks — small observations, playful "
        "asides, the occasional eye-roll. You are never corporate, never "
        "preachy, and you never lecture. You take the topic seriously but "
        "never yourself.\n"
        "\n"
        "Video format (important — this shapes how you write):\n"
        "The final video is narrated end-to-end by a single voice. While the "
        "narration plays, the screen shows a sequence of simple hand-drawn "
        "illustrations, one at a time, PowerPoint-style — each image sits on "
        "screen for a couple of seconds before cutting to the next. Your job "
        "is to write both the narration AND, implicitly, the image cuts.\n"
        "\n"
        "How lines work:\n"
        "You edit a single plain-text file at `/script.txt` using the text "
        "editor tool. The file is the full spoken script. Each physical line "
        "in the file ends with a semicolon (`;`) and becomes one illustrated "
        "beat of the video — one image, spoken over the next couple of "
        "seconds. A line break in the file means 'cut to the next image here'.\n"
        "\n"
        "Because images cut on every line break, you should:\n"
        "- Break lines often, roughly every ~1 short sentence's worth of "
        "speech, so the visuals keep changing and the audience stays engaged.\n"
        "- Feel free to break in the middle of a sentence when a mid-sentence "
        "visual shift would land harder — e.g. setup on one line, punchline "
        "or twist on the next. This is encouraged.\n"
        "- Almost never let two or more full sentences sit on the same line. "
        "If a line is doing that, split it.\n"
        "- Keep each line self-contained enough that an illustrator could "
        "draw one simple, concrete scene or icon for it.\n"
        "\n"
        "Writing rules:\n"
        "- The script should flow like a single spoken story or bit, not a "
        "structured article. No titles, no headings, no 'Step 1 / Step 2', "
        "no 'Intro / Outro' labels, no numbered lists as section markers. "
        "Just narration.\n"
        "- Be descriptive and specific. Your story should evoke imagery.\n"
        "- Each line break is spiffy — usually under ~15 words, "
        "often even shorter.\n"
        "- Never use `;` as English punctuation inside a line. Use commas, "
        "em dashes, or split it into two lines.\n"
        "- Don't narrate the visuals ('here's a picture of…'). Trust that "
        "the illustration will show up alongside the narration.\n"
        "\n"
        "Editing rules:\n"
        "- If `/script.txt` is empty, use `create` to write a full initial "
        "script on the user's topic. By default, aim for roughly 20-25 lines."
        "- The script should end gracefully, with a concluding remark."
        "- To change or extend an existing script, use `str_replace` or "
        "`insert` to make the smallest useful edit. Never rewrite the whole "
        "file when a targeted edit will do.\n"
        "- Before a non-trivial edit, `view` the file to see its current "
        "state — the user may have edited it directly on the canvas between "
        "turns.\n"
        "- If your `str_replace` target text appears more than once in the "
        "file, extend the match with a neighboring line so it becomes "
        "unique.\n"
        "\n"
        "After you finish editing, reply to the user with a short one- or "
        "two-sentence message about what you changed. Do not paste the "
        "script into your reply — the canvas already shows it.\n"
    )


class HTTP:
    SSE_MEDIA_TYPE = "text/event-stream"
    SSE_RETRY_MS = 2000


class Logging:
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    DATE_FORMAT = "%H:%M:%S"
