// Fix: Provide full implementation for application types.
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
  key?: string; // e.g., "11B" (Camelot wheel)
}

export interface Hotcue {
  num: number; // 1-4
  time: number; // in seconds
}

// Data structure for storing Hot Cues in the comment tag
export interface CueData {
    hotcues: Hotcue[];
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
  hotcues: Hotcue[];
  duration?: number;
}

export interface Playlist {
    id: string;
    name: string;
    trackIds: string[];
}

export type GroupKey = 'artist' | 'album' | 'none';

// Types for XML Converter
export interface CuePoint {
  timeMs: number;
  name: string;
  type: number; // e.g., Rekordbox type for HotCue, etc.
}

export interface Loop {
  startMs: number;
  endMs: number;
}

export interface GenericTrack {
  location: string;
  title?: string;
  artist?: string;
  album?: string;
  genre?: string;
  year?: string;
  bpm?: number;
  key?: string; // Camelot
  rating?: number;
  playCount?: number;
  cues: CuePoint[];
  loops: Loop[];
}

// Types for Smart Collections
export type RuleOperator = 
    | 'is' | 'is_not' | 'contains' | 'not_contains'
    | 'is_greater_than' | 'is_less_than' | 'is_in_range'
    | 'is_empty' | 'is_not_empty';

export interface Rule {
    id: string;
    field: keyof ID3Tags;
    operator: RuleOperator;
    value: string | number | [number, number];
}

export type RuleLogic = 'AND' | 'OR';

export interface SmartCollection {
    id: string;
    name: string;
    logic: RuleLogic;
    rules: Rule[];
}