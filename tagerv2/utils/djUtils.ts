
import { AudioFile } from '../types';

// Camelot Wheel Logic
const CAMELOT_KEYS = [
  '1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B', 
  '5A', '5B', '6A', '6B', '7A', '7B', '8A', '8B', 
  '9A', '9B', '10A', '10B', '11A', '11B', '12A', '12B'
];

/**
 * Returns a list of compatible Camelot keys for a given key.
 * Rules: Same key, +/- 1 hour on the wheel, relative major/minor.
 */
export const getCompatibleKeys = (key: string): string[] => {
  if (!key) return [];
  const normalizedKey = key.toUpperCase().trim();
  if (!CAMELOT_KEYS.includes(normalizedKey)) return [];

  const number = parseInt(normalizedKey.replace(/[AB]/, ''), 10);
  const letter = normalizedKey.slice(-1); // A or B

  const compatible: string[] = [];

  // 1. Exact Match
  compatible.push(normalizedKey);

  // 2. Relative Major/Minor (Swap letter)
  compatible.push(`${number}${letter === 'A' ? 'B' : 'A'}`);

  // 3. +/- 1 Hour on the wheel (Same letter)
  const prevNum = number === 1 ? 12 : number - 1;
  const nextNum = number === 12 ? 1 : number + 1;
  compatible.push(`${prevNum}${letter}`);
  compatible.push(`${nextNum}${letter}`);

  // Optional: Energy Boost (+2 hours) - often used by DJs
  // const boostNum = number + 2 > 12 ? number + 2 - 12 : number + 2;
  // compatible.push(`${boostNum}${letter}`);

  return compatible;
};

/**
 * Checks if two BPMs are within a mixable range (e.g., +/- 5%).
 */
export const isBpmCompatible = (bpm1: number | undefined, bpm2: number | undefined, rangePercent: number = 5): boolean => {
  if (!bpm1 || !bpm2) return false;
  const diff = Math.abs(bpm1 - bpm2);
  const threshold = (bpm1 * rangePercent) / 100;
  return diff <= threshold;
};

/**
 * Finds compatible tracks from a library based on a source track.
 */
export const findMixSuggestions = (sourceTrack: AudioFile, library: AudioFile[]): AudioFile[] => {
  const sourceTags = sourceTrack.fetchedTags || sourceTrack.originalTags;
  const sourceKey = sourceTags?.initialKey;
  const sourceBpm = sourceTags?.bpm;

  if (!sourceKey && !sourceBpm) return [];

  const compatibleKeys = sourceKey ? getCompatibleKeys(sourceKey) : [];

  return library.filter(track => {
    // Don't recommend itself
    if (track.id === sourceTrack.id) return false;

    const tags = track.fetchedTags || track.originalTags;
    if (!tags) return false;

    // Check Key Compatibility
    const keyMatch = !sourceKey || (tags.initialKey && compatibleKeys.includes(tags.initialKey));

    // Check BPM Compatibility (allow half/double time matches too)
    let bpmMatch = false;
    if (!sourceBpm) {
        bpmMatch = true;
    } else if (tags.bpm) {
        const tBpm = tags.bpm;
        bpmMatch = isBpmCompatible(sourceBpm, tBpm, 4) || 
                   isBpmCompatible(sourceBpm, tBpm * 2, 4) || 
                   isBpmCompatible(sourceBpm, tBpm / 2, 4);
    }

    return keyMatch && bpmMatch;
  });
};
