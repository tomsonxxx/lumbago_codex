// Fix: Correct import path
import { AudioFile, ProcessingState } from '../types';

export type SortKey = 'dateAdded' | 'originalName' | 'newName' | 'state' | 'bpm' | 'key' | 'time';

const stateOrder: Record<ProcessingState, number> = {
  [ProcessingState.PROCESSING]: 1,
  [ProcessingState.DOWNLOADING]: 2,
  [ProcessingState.PENDING]: 3,
  [ProcessingState.SUCCESS]: 4,
  [ProcessingState.ERROR]: 5,
};

// Camelot wheel order for sorting by key
const camelotKeyOrder: { [key: string]: number } = {
  '1B': 1, '8B': 2, '3B': 3, '10B': 4, '5B': 5, '12B': 6, '7B': 7, '2B': 8, '9B': 9, '4B': 10, '11B': 11, '6B': 12,
  '1A': 13, '8A': 14, '3A': 15, '10A': 16, '5A': 17, '12A': 18, '7A': 19, '2A': 20, '9A': 21, '4A': 22, '11A': 23, '6A': 24,
};

export const sortFiles = (
  files: AudioFile[],
  key: SortKey,
  direction: 'asc' | 'desc'
): AudioFile[] => {
  const sorted = files.sort((a, b) => {
    let comparison = 0;
    const tagsA = a.fetchedTags || a.originalTags;
    const tagsB = b.fetchedTags || b.originalTags;

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
      case 'bpm':
        comparison = (tagsA.bpm || 0) - (tagsB.bpm || 0);
        break;
      case 'key':
        const keyA = camelotKeyOrder[tagsA.key || ''] || 99;
        const keyB = camelotKeyOrder[tagsB.key || ''] || 99;
        comparison = keyA - keyB;
        break;
      case 'time':
        comparison = (a.duration || 0) - (b.duration || 0);
        break;
    }

    return comparison;
  });

  return direction === 'asc' ? sorted : sorted.reverse();
};