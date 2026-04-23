export type Track = {
  id: number;
  path?: string;
  title: string;
  artist: string;
  album?: string;
  year?: string;
  genre?: string;
  key?: string;
  bpm?: number;
  duration?: number;
  url?: string;
  hash?: string;
  fingerprint?: string;
};

export type ProviderConfig = {
  provider: "openai" | "gemini" | "grok" | "deepseek";
  api_key: string;
  base_url: string;
  model: string;
  priority: number;
  enabled: boolean;
};

export type FieldDecision = {
  field: string;
  old_value: string | number | null;
  new_value: string | number | null;
  winner_provider: string;
  confidence: number;
  accepted: boolean;
  reason: string;
};

export type ProviderResult = {
  provider: string;
  overall_confidence: number;
  values: Record<string, string | number>;
  error?: string | null;
};

export type AnalysisTrackItem = {
  track_id: number;
  path: string;
  title: string;
  artist: string;
  provider_chain: string;
  confidence: number;
  decisions: FieldDecision[];
  provider_results: ProviderResult[];
};

export type AnalysisJob = {
  id: string;
  status: "queued" | "running" | "completed" | "failed";
  policy: string;
  track_ids: number[];
  processed: number;
  total: number;
  items: AnalysisTrackItem[];
  error?: string;
};

export type ImportPreviewResult = {
  tracks: Track[];
  errors: string[];
};

export type ImportCommitResult = {
  imported: number;
  errors: string[];
};

export type DuplicateGroup = {
  key: string;
  similarity: number;
  tracks: Track[];
};

export type DuplicateAnalysisResult = {
  groups: DuplicateGroup[];
};

export type AnalysisApplyResult = {
  updated_tracks: number;
  applied_changes: number;
};
