import type {
  AnalysisApplyResult,
  AnalysisJob,
  DuplicateAnalysisResult,
  ImportCommitResult,
  ImportPreviewResult,
  ProviderConfig,
  Track,
  TrackUpdate,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getTracks(): Promise<Track[]> {
  const payload = await request<{ tracks: Track[] }>("/tracks");
  return payload.tracks;
}

export async function importPreview(folder: string): Promise<ImportPreviewResult> {
  return request<ImportPreviewResult>("/tracks/import-preview", {
    method: "POST",
    body: JSON.stringify({ folder, recursive: true }),
  });
}

export async function importCommit(paths: string[]): Promise<ImportCommitResult> {
  return request<ImportCommitResult>("/tracks/import-commit", {
    method: "POST",
    body: JSON.stringify({ paths }),
  });
}

export async function analyzeDuplicates(
  mode: "hash" | "fingerprint" | "metadata",
): Promise<DuplicateAnalysisResult> {
  return request<DuplicateAnalysisResult>("/duplicates/analyze", {
    method: "POST",
    body: JSON.stringify({ mode }),
  });
}

export async function getAiProviders(): Promise<ProviderConfig[]> {
  const payload = await request<{ providers: ProviderConfig[] }>("/ai/providers");
  return payload.providers;
}

export async function updateAiProviders(providers: ProviderConfig[]): Promise<ProviderConfig[]> {
  const payload = await request<{ providers: ProviderConfig[] }>("/ai/providers", {
    method: "PUT",
    body: JSON.stringify({ providers }),
  });
  return payload.providers;
}

export async function createAnalysisJob(trackIds: number[]): Promise<{ job_id: string; status: string }> {
  return request<{ job_id: string; status: string }>("/analysis/jobs", {
    method: "POST",
    body: JSON.stringify({ track_ids: trackIds, policy: "aggressive" }),
  });
}

export async function getAnalysisJob(jobId: string): Promise<AnalysisJob> {
  return request<AnalysisJob>(`/analysis/jobs/${jobId}`);
}

export async function applyAnalysisJob(jobId: string): Promise<AnalysisApplyResult> {
  return request<AnalysisApplyResult>(`/analysis/jobs/${jobId}/apply`, {
    method: "POST",
    body: JSON.stringify({ overrides: {}, source_prefix: "ai" }),
  });
}

export type TrackUpdateResult = { track: Track; warning?: string };

export async function updateTrack(path: string, update: TrackUpdate): Promise<TrackUpdateResult> {
  return request<TrackUpdateResult>(`/tracks/${encodeURIComponent(path)}`, {
    method: "PUT",
    body: JSON.stringify(update),
  });
}
