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

export async function generateScript(payload: GenerateScriptRequest): Promise<GenerateScriptResponse> {
  return fetchJson<GenerateScriptResponse>("/scripts/generate", {
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
