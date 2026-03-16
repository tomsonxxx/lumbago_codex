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
}

export type GroupKey = 'artist' | 'album' | 'none';