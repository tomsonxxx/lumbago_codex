
// Fix: Correct import path
import { AudioFile, ProcessingState } from '../types';

export type SortKey = 'dateAdded' | 'originalName' | 'newName' | 'state' | 'title' | 'artist' | 'album' | 'bpm' | 'key' | 'genre' | 'year' | 'rating';

export interface SortConfig {
    key: SortKey;
    direction: 'asc' | 'desc';
}

const stateOrder: Record<ProcessingState, number> = {
  [ProcessingState.PROCESSING]: 1,
  [ProcessingState.DOWNLOADING]: 2,
  [ProcessingState.PENDING]: 3,
  [ProcessingState.SUCCESS]: 4,
  [ProcessingState.ERROR]: 5,
};

const getValue = (file: AudioFile, key: SortKey): string | number => {
    const tags = file.fetchedTags || file.originalTags || {};
    
    switch (key) {
        case 'dateAdded': return file.dateAdded;
        case 'state': return stateOrder[file.state];
        case 'originalName': return file.file.name.toLowerCase();
        case 'newName': return (file.newName || file.file.name).toLowerCase();
        case 'title': return (tags.title || file.file.name).toLowerCase();
        case 'artist': return (tags.artist || '').toLowerCase();
        case 'album': return (tags.album || '').toLowerCase();
        case 'genre': return (tags.genre || '').toLowerCase();
        case 'year': return tags.year || '';
        case 'bpm': 
             // Handle BPM as number or string parsing
             const bpm = tags.bpm;
             if (typeof bpm === 'number') return bpm;
             if (typeof bpm === 'string') return parseFloat(bpm) || 0;
             return 0;
        case 'key': return (tags.initialKey || '').toLowerCase();
        case 'rating': return tags.rating || 0;
        default: return '';
    }
};

export const sortFiles = (
  files: AudioFile[],
  sortConfig: SortConfig[]
): AudioFile[] => {
  if (sortConfig.length === 0) return files;

  return [...files].sort((a, b) => {
    for (const { key, direction } of sortConfig) {
        const valA = getValue(a, key);
        const valB = getValue(b, key);

        if (valA < valB) {
            return direction === 'asc' ? -1 : 1;
        }
        if (valA > valB) {
            return direction === 'asc' ? 1 : -1;
        }
    }
    return 0;
  });
};
