import { AudioFile } from '../types';

export type DuplicateGroup = AudioFile[];

const normalizeString = (str?: string): string => {
    if (!str) return '';
    return str.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
};

/**
 * Finds duplicates based on tag comparison (artist and title).
 * This method is fast but less accurate.
 */
export const findDuplicatesByTags = (files: AudioFile[]): DuplicateGroup[] => {
    const groups: Record<string, AudioFile[]> = {};

    files.forEach(file => {
        const tags = file.fetchedTags || file.originalTags;
        const artist = normalizeString(tags.artist);
        const title = normalizeString(tags.title);

        if (artist && title) {
            const key = `${artist}-${title}`;
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(file);
        }
    });

    return Object.values(groups).filter(group => group.length > 1);
};

/**
 * Asynchronously calculates the SHA-256 hash of a file.
 * Reports progress via a callback.
 * @param file The file to hash.
 * @param onProgress Callback to report progress (0-1).
 * @returns The hex string of the file's hash.
 */
export const calculateFileHash = async (file: File, onProgress: (progress: number) => void): Promise<string> => {
    const buffer = await file.arrayBuffer();
    // Use the SubtleCrypto API available in modern browsers (and web workers) for hashing.
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    // Convert the byte array to a hex string.
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    // Simulate progress as digest is a one-shot operation
    onProgress(1);

    return hashHex;
};


/**
 * Finds duplicates based on file content hash (SHA-256).
 * This method is slow but 100% accurate.
 * Reports progress via a callback.
 * @param files The list of files to check.
 * @param onProgress Callback to report total progress (0-1).
 * @returns A promise that resolves to the groups of duplicates.
 */
export const findDuplicatesByHash = async (
    files: AudioFile[],
    onProgress: (progress: number) => void
): Promise<DuplicateGroup[]> => {
    const hashes: Record<string, AudioFile[]> = {};
    const totalFiles = files.length;
    let processedFiles = 0;

    for (const file of files) {
        try {
            const hash = await calculateFileHash(file.file, () => {}); // Individual progress not needed here
            if (!hashes[hash]) {
                hashes[hash] = [];
            }
            hashes[hash].push(file);
        } catch (error) {
            console.error(`Could not hash file ${file.file.name}:`, error);
        }
        processedFiles++;
        onProgress(processedFiles / totalFiles);
    }

    return Object.values(hashes).filter(group => group.length > 1);
};
