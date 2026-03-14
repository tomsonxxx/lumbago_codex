import { AudioFile } from '../types';

const camelotKeyOrder: { [key: string]: number } = {
  '1B': 1, '8B': 2, '3B': 3, '10B': 4, '5B': 5, '12B': 6, '7B': 7, '2B': 8, '9B': 9, '4B': 10, '11B': 11, '6B': 12,
  '1A': 13, '8A': 14, '3A': 15, '10A': 16, '5A': 17, '12A': 18, '7A': 19, '2A': 20, '9A': 21, '4A': 22, '11A': 23, '6A': 24,
};

const getKeyNumber = (key: string): number => parseInt(key.slice(0, -1), 10);
const getKeyMode = (key: string): 'A' | 'B' => key.slice(-1) as 'A' | 'B';

const areKeysCompatible = (key1: string, key2: string): boolean => {
    if (!key1 || !key2 || !camelotKeyOrder[key1] || !camelotKeyOrder[key2]) return false;
    
    const num1 = getKeyNumber(key1);
    const mode1 = getKeyMode(key1);
    const num2 = getKeyNumber(key2);
    const mode2 = getKeyMode(key2);

    // Same key
    if (num1 === num2 && mode1 === mode2) return true;
    
    // Switch modes (e.g., 5A -> 5B)
    if (num1 === num2 && mode1 !== mode2) return true;
    
    // One step up on the wheel (e.g., 5A -> 6A)
    if (mode1 === mode2 && (num2 === num1 + 1 || (num1 === 12 && num2 === 1))) return true;
    
    // One step down on the wheel (e.g., 5A -> 4A)
    if (mode1 === mode2 && (num2 === num1 - 1 || (num1 === 1 && num2 === 12))) return true;
    
    return false;
};

const getCompatibilityScore = (track1: AudioFile, track2: AudioFile): number => {
    const key1 = (track1.fetchedTags || track1.originalTags).key;
    const key2 = (track2.fetchedTags || track2.originalTags).key;
    const bpm1 = (track1.fetchedTags || track1.originalTags).bpm || 0;
    const bpm2 = (track2.fetchedTags || track2.originalTags).bpm || 0;

    let score = 0;

    // High score for perfect harmonic match
    if (key1 && key2 && areKeysCompatible(key1, key2)) {
        score += 100;
        // Bonus for staying in the same key
        if (key1 === key2) {
            score += 50;
        }
    }

    // Score for BPM proximity
    const bpmDiff = Math.abs(bpm1 - bpm2);
    if (bpmDiff <= 3) {
        score += 30; // Very close BPM
    } else if (bpmDiff <= 7) {
        score += 15; // Reasonably close
    }

    // Penalty for large BPM jumps, but less if it's a double/half time mix
    const bpmRatio = Math.max(bpm1, bpm2) / Math.min(bpm1, bpm2);
    if (bpmRatio > 1.1) { // More than 10% jump
        score -= 50;
    }
    if (bpmRatio > 1.8 && bpmRatio < 2.2) { // Double/half time is okay
        score += 40;
    }

    return score;
};

export const sortPlaylistIntelligently = (files: AudioFile[]): AudioFile[] => {
    if (files.length < 2) return files;
    
    const remainingFiles = [...files];
    const sortedPlaylist: AudioFile[] = [];

    // Find a good starting track (e.g., lowest BPM)
    let currentTrack = remainingFiles.sort((a, b) => {
        const bpmA = (a.fetchedTags || a.originalTags).bpm || 999;
        const bpmB = (b.fetchedTags || b.originalTags).bpm || 999;
        return bpmA - bpmB;
    }).shift()!;
    
    sortedPlaylist.push(currentTrack);

    while (remainingFiles.length > 0) {
        let bestNextTrack: AudioFile | null = null;
        let bestScore = -Infinity;
        let bestIndex = -1;

        remainingFiles.forEach((nextTrack, index) => {
            const score = getCompatibilityScore(currentTrack, nextTrack);
            if (score > bestScore) {
                bestScore = score;
                bestNextTrack = nextTrack;
                bestIndex = index;
            }
        });

        if (bestNextTrack) {
            currentTrack = bestNextTrack;
            sortedPlaylist.push(currentTrack);
            remainingFiles.splice(bestIndex, 1);
        } else {
            // If no compatible track is found, just take the next one
            currentTrack = remainingFiles.shift()!;
            sortedPlaylist.push(currentTrack);
        }
    }

    return sortedPlaylist;
};
