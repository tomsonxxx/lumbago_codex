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
  trackNumber?: string;
  albumArtist?: string;
  composer?: string;
  copyright?: string;
  encodedBy?: string;
  originalArtist?: string;
  discNumber?: string;
  bpm?: number;
  key?: string;
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
  handle?: any;
  webkitRelativePath?: string;
  duration?: number;
  rating?: number;
}

export type GroupKey = 'artist' | 'album' | 'none';

export type ViewType = 'dashboard' | 'library' | 'import' | 'duplicates' | 'settings' | 'player' | 'tagger' | 'converter';

export interface ActivityEntry {
  id: string;
  type: 'import' | 'ai_tag' | 'duplicate_found' | 'tags_edited' | 'export';
  message: string;
  timestamp: number;
  fileCount?: number;
}

export interface LibraryFilters {
  genre: string | null;
  status: ProcessingState | null;
  bpmMin: number | null;
  bpmMax: number | null;
  key: string | null;
  rating: number | null;
}

export interface DuplicateGroup {
  id: string;
  confidence: 'very_high' | 'high' | 'medium';
  fileIds: string[];
}
