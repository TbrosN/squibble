import type {
  ChatRequest,
  ChatResponse,
  ScriptLine,
  StopMotionResponse,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    try {
      const body = await response.json();
      if (body && typeof body.error === "string") {
        message = body.error;
      }
    } catch {
      // fall through
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  baseUrl: API_BASE_URL,

  assetUrl(path: string | null | undefined): string | undefined {
    if (!path) return undefined;
    if (/^https?:\/\//i.test(path)) return path;
    return `${API_BASE_URL}${path}`;
  },

  async scriptChat(body: ChatRequest): Promise<ChatResponse> {
    return request<ChatResponse>("/script/chat", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async startGeneration(script: ScriptLine[]): Promise<{ job_id: string }> {
    return request<{ job_id: string }>("/generate/start", {
      method: "POST",
      body: JSON.stringify({ script }),
    });
  },

  async cancelGeneration(jobId: string): Promise<void> {
    await request<{ ok: true }>(`/generate/cancel/${jobId}`, {
      method: "POST",
    });
  },

  async createStopMotion(
    file: File,
    stylePrompt: string,
    framesPerSecond: number,
  ): Promise<StopMotionResponse> {
    const form = new FormData();
    form.append("file", file);
    form.append("style_prompt", stylePrompt);
    form.append("frames_per_second", String(framesPerSecond));

    const response = await fetch(`${API_BASE_URL}/stopmotion/create`, {
      method: "POST",
      body: form,
    });

    if (!response.ok) {
      let message = "Couldn't restyle the video. Please try a shorter clip.";
      try {
        const body = await response.json();
        if (body && typeof body.error === "string") {
          message = body.error;
        }
      } catch {
        // fall through
      }
      throw new ApiError(message, response.status);
    }

    return (await response.json()) as StopMotionResponse;
  },

  streamUrl(jobId: string): string {
    return `${API_BASE_URL}/generate/stream/${jobId}`;
  },

  downloadUrl(jobId: string): string {
    return `${API_BASE_URL}/generate/download/${jobId}`;
  },
};
