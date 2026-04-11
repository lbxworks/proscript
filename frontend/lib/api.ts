import { API_BASE_URL } from "@/lib/constants";
import type {
  GenerateScriptRequest,
  GenerateScriptResponse,
  LibraryDocumentsResponse,
  LibraryHealthResponse,
  LibraryRebuildResponse,
  LibraryUploadResponse,
  ReviewScriptRequest,
  ReviewScriptResponse,
  TalentDeleteResponse,
  TalentMutationRequest,
  TalentMutationResponse,
  TalentsResponse,
  TrendsResponse,
  WorkflowErrorEvent,
  WorkflowProgressEvent,
} from "@/lib/schemas";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export class WorkflowStreamTimeoutError extends Error {
  constructor(message = "Villy 思考了太久，可能遇到了意外情况。") {
    super(message);
    this.name = "WorkflowStreamTimeoutError";
  }
}

export class WorkflowStreamAbortedError extends Error {
  constructor(message = "本次任务已取消。") {
    super(message);
    this.name = "WorkflowStreamAbortedError";
  }
}

type StreamOptions<Result> = {
  method?: "GET" | "POST";
  body?: string;
  signal?: AbortSignal;
  timeoutMs?: number;
  onProgress?: (event: WorkflowProgressEvent) => void;
  onError?: (event: WorkflowErrorEvent) => void;
  onComplete?: (result: Result) => void;
};

function parseSseChunk(block: string): { event: string; data: unknown } | null {
  const lines = block.split("\n");
  let event = "message";
  const dataLines: string[] = [];

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    if (!line) {
      continue;
    }
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (!dataLines.length) {
    return null;
  }

  return {
    event,
    data: JSON.parse(dataLines.join("\n")),
  };
}

async function streamSse<Result>(path: string, options: StreamOptions<Result>): Promise<Result> {
  const controller = new AbortController();
  let externallyAborted = false;
  let timedOut = false;
  let timeoutHandle: number | null = null;

  const resetTimeout = () => {
    if (timeoutHandle !== null) {
      window.clearTimeout(timeoutHandle);
    }
    timeoutHandle = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, options.timeoutMs ?? 120_000);
  };

  const handleAbort = () => {
    externallyAborted = true;
    controller.abort();
  };

  options.signal?.addEventListener("abort", handleAbort);

  try {
    resetTimeout();
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method ?? "GET",
      body: options.body,
      cache: "no-store",
      signal: controller.signal,
      headers: {
        Accept: "text/event-stream",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
      },
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `Request failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("浏览器没有收到可读取的流式响应。");
    }

    const decoder = new TextDecoder();
    let buffer = "";
    let finalResult: Result | null = null;

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      resetTimeout();
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

      let separatorIndex = buffer.indexOf("\n\n");
      while (separatorIndex !== -1) {
        const block = buffer.slice(0, separatorIndex).trim();
        buffer = buffer.slice(separatorIndex + 2);
        separatorIndex = buffer.indexOf("\n\n");

        if (!block) {
          continue;
        }

        const parsed = parseSseChunk(block);
        if (!parsed) {
          continue;
        }

        if (parsed.event === "progress") {
          options.onProgress?.(parsed.data as WorkflowProgressEvent);
          continue;
        }

        if (parsed.event === "error") {
          const errorEvent = parsed.data as WorkflowErrorEvent;
          options.onError?.(errorEvent);
          throw new Error(errorEvent.message || "流程执行失败。");
        }

        if (parsed.event === "complete") {
          finalResult = (parsed.data as { result: Result }).result;
          options.onComplete?.(finalResult);
        }
      }
    }

    if (finalResult === null) {
      if (timedOut) {
        throw new WorkflowStreamTimeoutError();
      }
      if (externallyAborted) {
        throw new WorkflowStreamAbortedError();
      }
      throw new Error("流式任务提前结束，请重新开始。");
    }

    return finalResult;
  } catch (error) {
    if (timedOut) {
      throw new WorkflowStreamTimeoutError();
    }
    if (externallyAborted) {
      throw new WorkflowStreamAbortedError();
    }
    throw error;
  } finally {
    if (timeoutHandle !== null) {
      window.clearTimeout(timeoutHandle);
    }
    options.signal?.removeEventListener("abort", handleAbort);
  }
}

export async function generateScript(payload: GenerateScriptRequest): Promise<GenerateScriptResponse> {
  return fetchJson<GenerateScriptResponse>("/scripts/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function streamGenerateScript(
  payload: GenerateScriptRequest,
  options: Omit<StreamOptions<GenerateScriptResponse>, "body" | "method"> = {},
): Promise<GenerateScriptResponse> {
  return streamSse<GenerateScriptResponse>("/scripts/generate/stream", {
    ...options,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getTalents(): Promise<TalentsResponse> {
  return fetchJson<TalentsResponse>("/talents");
}

export async function createTalent(payload: TalentMutationRequest): Promise<TalentMutationResponse> {
  return fetchJson<TalentMutationResponse>("/talents", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateTalent(talentId: number, payload: TalentMutationRequest): Promise<TalentMutationResponse> {
  return fetchJson<TalentMutationResponse>(`/talents/${talentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteTalent(talentId: number): Promise<TalentDeleteResponse> {
  return fetchJson<TalentDeleteResponse>(`/talents/${talentId}`, {
    method: "DELETE",
  });
}

export async function reviewScript(payload: ReviewScriptRequest): Promise<ReviewScriptResponse> {
  return fetchJson<ReviewScriptResponse>("/scripts/review", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function streamReviewScript(
  payload: ReviewScriptRequest,
  options: Omit<StreamOptions<ReviewScriptResponse>, "body" | "method"> = {},
): Promise<ReviewScriptResponse> {
  return streamSse<ReviewScriptResponse>("/scripts/review/stream", {
    ...options,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getTrends(params: {
  topic?: string;
  target_country: string;
  target_platform: string;
  distribution_mode: string;
  product_category: string;
  target_languages: string[];
  refresh_videos?: boolean;
  refresh_industry?: boolean;
}): Promise<TrendsResponse> {
  const query = new URLSearchParams();
  if (params.topic) {
    query.set("topic", params.topic);
  }
  query.set("target_country", params.target_country);
  query.set("target_platform", params.target_platform);
  query.set("distribution_mode", params.distribution_mode);
  query.set("product_category", params.product_category);
  if (params.refresh_videos) {
    query.set("refresh_videos", "true");
  }
  if (params.refresh_industry) {
    query.set("refresh_industry", "true");
  }
  for (const language of params.target_languages) {
    query.append("target_languages", language);
  }
  return fetchJson<TrendsResponse>(`/trends?${query.toString()}`);
}

export async function streamTrends(
  params: {
    topic?: string;
    target_country: string;
    target_platform: string;
    distribution_mode: string;
    product_category: string;
    target_languages: string[];
    refresh_videos?: boolean;
    refresh_industry?: boolean;
  },
  options: Omit<StreamOptions<TrendsResponse>, "body" | "method"> = {},
): Promise<TrendsResponse> {
  const query = new URLSearchParams();
  if (params.topic) {
    query.set("topic", params.topic);
  }
  query.set("target_country", params.target_country);
  query.set("target_platform", params.target_platform);
  query.set("distribution_mode", params.distribution_mode);
  query.set("product_category", params.product_category);
  if (params.refresh_videos) {
    query.set("refresh_videos", "true");
  }
  if (params.refresh_industry) {
    query.set("refresh_industry", "true");
  }
  for (const language of params.target_languages) {
    query.append("target_languages", language);
  }

  return streamSse<TrendsResponse>(`/trends/stream?${query.toString()}`, {
    ...options,
    method: "GET",
  });
}

export async function getLibraryHealth(initialize = false): Promise<LibraryHealthResponse> {
  return fetchJson<LibraryHealthResponse>(`/library/health?initialize=${String(initialize)}`);
}

export async function getLibraryDocuments(): Promise<LibraryDocumentsResponse> {
  return fetchJson<LibraryDocumentsResponse>("/library/documents");
}

export async function rebuildLibrary(): Promise<LibraryRebuildResponse> {
  return fetchJson<LibraryRebuildResponse>("/library/rebuild", {
    method: "POST",
  });
}

export async function uploadLibraryDocument(payload: {
  file: File;
  title: string;
  category: string;
  market: string;
  region: string;
  platform: string;
  language: string;
  source_url: string;
  notes: string;
  priority: string;
}): Promise<LibraryUploadResponse> {
  const formData = new FormData();
  formData.set("file", payload.file);
  formData.set("title", payload.title);
  formData.set("category", payload.category);
  formData.set("market", payload.market);
  formData.set("region", payload.region);
  formData.set("platform", payload.platform);
  formData.set("language", payload.language);
  formData.set("source_url", payload.source_url);
  formData.set("notes", payload.notes);
  formData.set("priority", payload.priority);

  const response = await fetch(`${API_BASE_URL}/library/upload`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<LibraryUploadResponse>;
}
