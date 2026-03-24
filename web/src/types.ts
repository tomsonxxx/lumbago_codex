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
