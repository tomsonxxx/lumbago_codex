
import { AudioFile, ID3Tags } from '../types';
import { calculateSimilarity } from './stringUtils';

/**
 * Normalizes a string for comparison by converting to lowercase and removing extra whitespace and special chars.
 */
const normalize = (str: string | undefined): string => {
    return str ? str.toLowerCase().trim().replace(/[^a-z0-9 ]/gi, '').replace(/\s+/g, ' ') : '';
};

/**
 * Scans a list of audio files and groups them into sets of duplicates.
 * Uses exact matching for Artist+Title first, then fuzzy matching for fallback.
 */
export const findDuplicateSets = (files: AudioFile[]): Map<string, AudioFile[]> => {
    const duplicateSets = new Map<string, AudioFile[]>();
    const processedIds = new Set<string>();

    // 1. Exact / Normalized Match Grouping
    const fingerprintMap = new Map<string, AudioFile[]>();

    files.forEach(file => {
        const tags = file.fetchedTags || file.originalTags;
        // Fallback to filename if tags missing
        const artist = normalize(tags.artist || tags.albumArtist) || 'unknown';
        const title = normalize(tags.title) || normalize(file.file.name);
        
        // Simple fingerprint
        const key = `${artist}|${title}`;
        
        if (!fingerprintMap.has(key)) {
            fingerprintMap.set(key, []);
        }
        fingerprintMap.get(key)!.push(file);
    });

    // 2. Process Exact Matches
    fingerprintMap.forEach((group, key) => {
        if (group.length > 1) {
            const setId = `dup-exact-${key.replace(/[^a-z0-9]/gi, '').slice(0, 20)}-${Date.now()}`;
            duplicateSets.set(setId, group);
            group.forEach(f => processedIds.add(f.id));
        }
    });

    // 3. Fuzzy Matching (O(n^2) - be careful with large libraries, maybe limit to files with same Artist)
    // We only check files that are NOT already in a duplicate set
    const remainingFiles = files.filter(f => !processedIds.has(f.id));
    
    // Optimization: Group by Artist first to reduce comparisons
    const artistGroups: Record<string, AudioFile[]> = {};
    remainingFiles.forEach(f => {
        const artist = normalize(f.fetchedTags?.artist || f.originalTags?.artist || 'unknown');
        if (!artistGroups[artist]) artistGroups[artist] = [];
        artistGroups[artist].push(f);
    });

    Object.values(artistGroups).forEach(group => {
        if (group.length < 2) return;

        for (let i = 0; i < group.length; i++) {
            if (processedIds.has(group[i].id)) continue;

            const duplicates = [group[i]];
            const titleA = normalize(group[i].fetchedTags?.title || group[i].originalTags?.title || group[i].file.name);

            for (let j = i + 1; j < group.length; j++) {
                if (processedIds.has(group[j].id)) continue;

                const titleB = normalize(group[j].fetchedTags?.title || group[j].originalTags?.title || group[j].file.name);
                
                // Fuzzy Threshold 0.85 (85% similar)
                if (calculateSimilarity(titleA, titleB) > 0.85) {
                    duplicates.push(group[j]);
                    processedIds.add(group[j].id);
                }
            }

            if (duplicates.length > 1) {
                const setId = `dup-fuzzy-${duplicates[0].id}`;
                duplicateSets.set(setId, duplicates);
                processedIds.add(group[i].id);
            }
        }
    });

    return duplicateSets;
};
