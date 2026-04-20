export type ScriptLine = {
  id: number;
  line: string;
  image_prompt: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatRequest = {
  messages: ChatMessage[];
  selected_lines: number[];
  current_script: ScriptLine[];
};

export type ChatResponse = {
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
