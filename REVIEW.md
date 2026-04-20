[BUG] Cancel returns to Stage 1 before the backend confirms cancellation. `useGeneration.cancel()` closes the SSE stream and sets the UI to `cancelled` immediately, so a failed cancel request or an in-flight line can keep generating after the user thinks the job is stopped.
[BUG] A malformed Claude response can wipe out the whole script. `ScriptService._parse_response()` accepts missing or empty `script` data, and the frontend then replaces the full canvas with that result instead of surfacing an error.
[BUG] Generation input is under-validated. `/generate/start` only checks that the script array is non-empty, so duplicate line ids can overwrite `audio_{index}` / `image_{index}` files and blank `image_prompt` values can slip into generation.

[UX] The empty Script Studio has no manual-first path. When there are no lines, the UI only shows helper copy, so users cannot add or paste their first line directly even though the spec calls for a full-canvas editable script editor.
[UX] A failed generation start still yanks the user into Stage 2. `page.tsx` switches to Generation Studio before `generation.start()` succeeds, which leaves the user on an empty error state instead of keeping them in Script Studio.
[UX] The red `Cancel` action is not always visible in Generation Studio. It disappears outside the `starting` / `running` phases even though the spec says both `← Back to Script` and `Cancel` should stay persistently visible.
[UX] The slide preview does not match the spec's "audio over image" feel. `SlidePreviewModal` renders standard audio controls below the image rather than presenting the audio as part of a lightweight full-image preview.
[UX] SSE failures do not produce a user-facing recovery state. `useGeneration` leaves `EventSource.onerror` empty, so a dropped stream can leave the grid sitting in `running` with no explanation or retry path.

[STYLE] `useGeneration` carries dead state. `finalUrl` is stored and updated, but nothing in the app ever reads it, which violates the spec's dead-code policy.
[STYLE] `VideoService` hardcodes ffmpeg details that the spec says should live in `constants.py`. The ffmpeg binary name, concat filename, part filename pattern, and render filter string are all embedded inline.
[STYLE] `ScriptService` falls back to raw dict payloads for Anthropic messages. That works at the SDK boundary, but it is not consistent with the spec's "modeled data over raw dicts" rule.
