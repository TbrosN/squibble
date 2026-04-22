export type ScriptLine = {
  id: number;
  line: string;
};

// UI-only type: the chat log shown to the user. The server no longer accepts
// prior messages — it keeps its own rolling history keyed by script_id. This
// type exists purely so the chat bar can render the running conversation.
export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatRequest = {
  message: string;
  // Opaque handle for the ongoing draft. Null on the first turn; server
  // mints and returns one, client echoes it back on subsequent turns.
  script_id: string | null;
  canvas_lines: string[];
  selected_lines: number[];
};

export type ChatResponse = {
  script_id: string;
  reply: string;
  script: ScriptLine[];
};

export type LineGenerationStatus =
  | "pending"
  | "generating"
  | "done"
  | "error";

export type SlideAsset = {
  id: number;
  line: string;
  status: LineGenerationStatus;
  imageUrl?: string;
  audioUrl?: string;
  duration?: number;
};

export type SSEEventType =
  | "line_update"
  | "complete"
  | "cancelled"
  | "error";

export type LineUpdateEvent = {
  type: "line_update";
  line_id: number;
  status: LineGenerationStatus;
  image_url?: string | null;
  audio_url?: string | null;
  duration?: number | null;
};

export type CompleteEvent = {
  type: "complete";
  final_url: string;
};

export type CancelledEvent = {
  type: "cancelled";
};

export type ErrorEvent = {
  type: "error";
  line_id?: number | null;
  message: string;
};

export type SSEEvent =
  | LineUpdateEvent
  | CompleteEvent
  | CancelledEvent
  | ErrorEvent;

export type Stage = "script" | "generation";
