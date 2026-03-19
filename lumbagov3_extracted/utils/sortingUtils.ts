
import { AudioFile, ProcessingState } from '../types';

export type SortKey = 'dateAdded' | 'originalName' | 'newName' | 'state' | 'artist' | 'title' | 'album' | 'bpm' | 'key' | 'year' | 'genre';

const stateOrder: Record<ProcessingState, number> = {
  [ProcessingState.PROCESSING]: 1,
  [ProcessingState.DOWNLOADING]: 2,
  [ProcessingState.PENDING]: 3,
  [ProcessingState.SUCCESS]: 4,
  [ProcessingState.ERROR]: 5,
};

export const sortFiles = (
  files: AudioFile[],
  key: SortKey,
  direction: 'asc' | 'desc'
): AudioFile[] => {
  const sorted = files.sort((a, b) => {
    let comparison = 0;

    // Helper to get tag value from fetchedTags or fallback to originalTags
    const getTag = (file: AudioFile, field: keyof import('../types').ID3Tags) => {
        return file.fetchedTags?.[field] || file.originalTags?.[field];
    };

    switch (key) {
      case 'dateAdded':
        comparison = a.dateAdded - b.dateAdded;
        break;
      case 'originalName':
        comparison = a.file.name.localeCompare(b.file.name, undefined, { numeric: true, sensitivity: 'base' });
        break;
      case 'newName':
        const nameA = a.newName || a.file.name;
        const nameB = b.newName || b.file.name;
        comparison = nameA.localeCompare(nameB, undefined, { numeric: true, sensitivity: 'base' });
        break;
      case 'state':
        comparison = stateOrder[a.state] - stateOrder[b.state];
        break;
      
      // Metadata sorting
      case 'artist':
        const artistA = getTag(a, 'artist') || '';
        const artistB = getTag(b, 'artist') || '';
        comparison = String(artistA).localeCompare(String(artistB), undefined, { sensitivity: 'base' });
        break;
      case 'title':
        const titleA = getTag(a, 'title') || a.file.name;
        const titleB = getTag(b, 'title') || b.file.name;
        comparison = String(titleA).localeCompare(String(titleB), undefined, { sensitivity: 'base' });
        break;
      case 'album':
        const albumA = getTag(a, 'album') || '';
        const albumB = getTag(b, 'album') || '';
        comparison = String(albumA).localeCompare(String(albumB), undefined, { sensitivity: 'base' });
        break;
      case 'genre':
        const genreA = getTag(a, 'genre') || '';
        const genreB = getTag(b, 'genre') || '';
        comparison = String(genreA).localeCompare(String(genreB), undefined, { sensitivity: 'base' });
        break;
      case 'year':
        const yearA = parseInt(String(getTag(a, 'year') || '0'));
        const yearB = parseInt(String(getTag(b, 'year') || '0'));
        comparison = yearA - yearB;
        break;
      case 'bpm':
        const bpmA = Number(getTag(a, 'bpm')) || 0;
        const bpmB = Number(getTag(b, 'bpm')) || 0;
        comparison = bpmA - bpmB;
        break;
      case 'key':
        const keyA = getTag(a, 'initialKey') || '';
        const keyB = getTag(b, 'initialKey') || '';
        comparison = String(keyA).localeCompare(String(keyB), undefined, { numeric: true });
        break;
    }

    return comparison;
  });

  return direction === 'asc' ? sorted : sorted.reverse();
};
