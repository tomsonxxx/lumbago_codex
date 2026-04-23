export enum ProcessingState {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  DOWNLOADING = 'DOWNLOADING',
  SUCCESS = 'SUCCESS',
  ERROR = 'ERROR',
}

export interface ID3Tags {
  artist?: string;
  title?: string;
  album?: string;
  year?: string;
  genre?: string;
  albumCoverUrl?: string;
  mood?: string;
  comments?: string;
  bitrate?: number;
  sampleRate?: number;
  trackNumber?: string; // Can be "1" or "1/12"
  albumArtist?: string;
  composer?: string;
  copyright?: string;
  encodedBy?: string;
  originalArtist?: string;
  discNumber?: string; // Can be "1" or "1/2"
  bpm?: number;
  key?: string;
}

export interface SourceProbeResult {
  source: 'google' | 'beatport' | 'traxsource' | 'discogs' | 'juno';
  status: 'hit' | 'miss' | 'error';
  query: string;
  detail?: string;
  url?: string;
}

export interface TagFieldConfidence {
  field: keyof ID3Tags;
  confidence: number;
  byProvider: Record<string, number>;
}

export interface DataOrigin {
  timestamp: string;
  providers: string[];
  modelVersions: Record<string, string>;
  sources: SourceProbeResult[];
  fieldConfidence: TagFieldConfidence[];
}

export interface PipelineError {
  code:
    | 'PIPELINE_UNEXPECTED'
    | 'LOCAL_PARSE_FAILED'
    | 'SOURCE_PROBE_FAILED'
    | 'AI_PROVIDER_FAILED'
    | 'CONSENSUS_FAILED'
    | 'WRITE_FAILED';
  message: string;
  step: 1 | 2 | 3 | 4 | 5 | 6;
  retriable: boolean;
  details?: string;
}

export interface TaggingDecision {
  proposedTags: ID3Tags;
  acceptedFields: (keyof ID3Tags)[];
  rejectedFields: (keyof ID3Tags)[];
  provenance: DataOrigin;
}

export interface SmartTagRun {
  runId: string;
  startedAt: string;
  finishedAt?: string;
  status: 'PROCESSING' | 'SUCCESS' | 'ERROR';
  attempts: number;
  decision?: TaggingDecision;
  error?: PipelineError;
}

export interface AudioFile {
  id: string;
  file: File;
  state: ProcessingState;
  originalTags: ID3Tags;
  fetchedTags?: ID3Tags;
  newName?: string;
  isSelected?: boolean;
  errorMessage?: string;
  dateAdded: number;
  handle?: any; // FileSystemFileHandle for direct saving
  webkitRelativePath?: string; // The relative path of the file within the directory
  smartTagRun?: SmartTagRun;
  retryCount?: number;
}

export type GroupKey = 'artist' | 'album' | 'none';
