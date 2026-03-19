
import { ID3Tags, AudioFile } from '../types';

const CACHE_PREFIX = 'lumbago_ai_cache_v1_';

/**
 * Generates a unique fingerprint for a file based on its metadata.
 * We use name + size + lastModified to be reasonably sure it's the same file
 * without reading the entire binary content (which is slow).
 */
const generateFileFingerprint = (file: File): string => {
  return `${file.name}_${file.size}_${file.lastModified}`;
};

/**
 * Saves AI analysis result to local storage.
 */
export const cacheAnalysisResult = (file: File, tags: ID3Tags): void => {
  try {
    const key = CACHE_PREFIX + generateFileFingerprint(file);
    // Add a timestamp to the cache entry if we want to implement expiration later
    const entry = {
      timestamp: Date.now(),
      tags: tags
    };
    localStorage.setItem(key, JSON.stringify(entry));
  } catch (e) {
    console.warn("Failed to save to cache (likely quota exceeded):", e);
    // Optionally clear old cache entries here
  }
};

/**
 * Retrieves cached analysis result if it exists.
 */
export const getCachedAnalysis = (file: File): ID3Tags | null => {
  try {
    const key = CACHE_PREFIX + generateFileFingerprint(file);
    const cached = localStorage.getItem(key);
    
    if (!cached) return null;
    
    const entry = JSON.parse(cached);
    // We could check for expiration here (e.g., if (Date.now() - entry.timestamp > 7 days)...)
    
    // Mark the data source as cached
    return { ...entry.tags, dataOrigin: 'cache' };
  } catch (e) {
    return null;
  }
};

/**
 * Clears the entire AI cache.
 */
export const clearAnalysisCache = (): void => {
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith(CACHE_PREFIX)) {
      localStorage.removeItem(key);
    }
  });
};