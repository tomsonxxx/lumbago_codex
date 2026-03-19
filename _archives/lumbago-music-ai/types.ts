
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
  
  // DJ / Technical Fields
  bpm?: number;
  initialKey?: string;
  energy?: number; // 1-10
  danceability?: number; // 1-10
  rating?: number;
  
  // Advanced AI Fields
  confidence?: 'high' | 'medium' | 'low';
  isrc?: string;
  releaseType?: 'album' | 'single' | 'compilation' | 'ep' | 'remix';
  recordLabel?: string;
  dataOrigin?: 'ai-inference' | 'google-search' | 'file-metadata' | 'cache';
}

export interface CuePoint {
  id: number;
  time: number;
  color: string;
  label?: string;
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
  handle?: any; // FileSystemFileHandle
  webkitRelativePath?: string;
  duplicateSetId?: string;
  cues?: CuePoint[];
}

export interface Playlist {
  id: string;
  name: string;
  trackIds: string[];
  createdAt: number;
}

export interface AnalysisSettings {
  fields: {
    bpm: boolean;
    key: boolean;
    genre: boolean;
    year: boolean;
    label: boolean;
    energy: boolean;
    danceability: boolean;
    mood: boolean;
    isrc: boolean;
    album_artist: boolean;
    composer: boolean;
  };
  mode: 'fast' | 'accurate' | 'creative';
}
