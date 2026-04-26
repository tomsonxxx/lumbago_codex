
import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { AudioFile, ID3Tags } from '../types';
import { getCachedAnalysis, cacheAnalysisResult } from './cacheService';

export type AIProvider = 'gemini' | 'grok' | 'openai';

export interface ApiKeys {
  grok: string;
  openai: string;
}

// --- SYSTEM INSTRUCTIONS ---
const getSystemInstruction = () => {
  return `You are "Lumbago Supervisor", an elite music archivist and DJ librarian AI.
Your goal is to repair, organize, and enrich metadata for music files with professional accuracy.

DATA SOURCES & VERIFICATION:
1. Use the provided filename and any existing (possibly partial or broken) metadata as your primary clues.
2. Use Google Search to verify all details: official release titles, artist spelling, release year, record label, and original genre.
3. For DJ-specific data, research the track on platforms like Beatport, Traxsource, Discogs, or Juno Download to find accurate BPM and Initial Key (musical key).

JSON STRUCTURE - return an array of objects with these fields (if found):
- title: string (official title, clean of version info unless part of title)
- artist: string (primary artist and featured artists)
- album: string (official album or single name)
- year: number (YYYY)
- genre: string (specific genre like 'Deep House', 'Techno', 'Indie Rock')
- bpm: number (accurate integer or float)
- initialKey: string (Camelot or standard musical key, e.g., '8A' or 'Am')
- recordLabel: string (official label)
- albumArtist: string
- trackNumber: string (e.g. '01' or '1/12')
- discNumber: string
- comments: string (brief description or source info)
- mood: string (energy level or vibe like 'Dark', 'Euphoric', 'Chill')

IMPORTANT RULES:
- Return ONLY a valid JSON Array.
- Values must be accurate. If a field cannot be found with high confidence, omit it or leave it as null/empty string rather than hallucinating.
- Do not repeat tags that are obviously correct, but fix those that are clearly formatted poorly.
- Always include 'confidence' field ('high', 'medium', 'low') per track.
`;
};

// --- HELPER FUNCTIONS ---
const callGeminiWithRetry = async (
    apiCall: () => Promise<GenerateContentResponse>,
    maxRetries = 3
): Promise<GenerateContentResponse> => {
    let lastError: Error | null = null;
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await apiCall();
        } catch (error: any) {
            lastError = error;
            // Immediate throw for auth/config errors
            if (error.status === 400 || error.status === 401 || error.status === 403) throw error;
            // Wait with exponential backoff
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
    throw lastError || new Error("API call failed after retries");
};

// --- CORE ANALYZER (Batch) ---
export const smartBatchAnalyze = async (
    files: AudioFile[],
    provider: AIProvider,
    apiKeys: ApiKeys,
    forceUpdate: boolean = false,
    analysisSettings?: any
): Promise<ID3Tags[]> => {
    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    // Use analysisSettings to inform the prompt if needed, here just logging to avoid lint error
    if (analysisSettings) console.log("Applying analysis settings:", Object.keys(analysisSettings.fields).filter(k => analysisSettings.fields[k]));
    
    const finalResultsMap: Record<string, ID3Tags> = {};
    const filesToFetch: AudioFile[] = [];

    // Cache Check
    if (!forceUpdate) {
        files.forEach(f => {
            const cached = getCachedAnalysis(f.file);
            if (cached) finalResultsMap[f.id] = cached;
            else filesToFetch.push(f);
        });
    } else {
        files.forEach(f => filesToFetch.push(f));
    }

    if (filesToFetch.length === 0) return files.map(f => finalResultsMap[f.id]);

    // Batching logic: process max 10 files per AI call to keep prompt manageable and within context limits
    const batchSize = 10;
    for (let i = 0; i < filesToFetch.length; i += batchSize) {
        const batch = filesToFetch.slice(i, i + batchSize);
        
        const filesContext = batch.map(f => {
            const t = f.originalTags || {};
            return {
                id: f.id,
                filename: f.file.name,
                path: f.webkitRelativePath,
                existingTags: {
                    title: t.title,
                    artist: t.artist,
                    album: t.album,
                    year: t.year,
                    genre: t.genre,
                    bpm: t.bpm,
                    key: t.initialKey
                }
            };
        });

        const prompt = `Perform intensive metadata research and correction for these music files. 
Verify details online using Google Search.
FILES TO ANALYZE:
${JSON.stringify(filesContext, null, 2)}

Return the results as a JSON array corresponding to the order of files provided.`;

        try {
            const response = await callGeminiWithRetry(() => 
                ai.models.generateContent({
                    model: "gemini-3-flash-preview",
                    contents: prompt,
                    config: {
                        systemInstruction: getSystemInstruction(),
                        tools: [{ googleSearch: {} }],
                        responseMimeType: "application/json"
                    }
                })
            );
            
            const text = response.text || "[]";
            let parsed: any[] = [];
            try {
                 // Try to strip potential markdown code blocks if the model fails responseMimeType
                 const jsonMatch = text.match(/\[[\s\S]*\]/);
                 parsed = JSON.parse(jsonMatch ? jsonMatch[0] : text);
            } catch (e) {
                 console.error("JSON Parse Error in batch", text);
            }
            
            batch.forEach((f, index) => {
                const res = parsed[index] || {};
                const tag: ID3Tags = { 
                    ...f.originalTags, 
                    ...res, 
                    dataOrigin: 'ai-inference',
                    fetchedAt: Date.now()
                };
                // Cache results
                cacheAnalysisResult(f.file, tag);
                finalResultsMap[f.id] = tag;
            });

        } catch (e) {
            console.error("Batch sub-group failed", e);
            batch.forEach(f => {
                finalResultsMap[f.id] = f.fetchedTags || f.originalTags;
            });
        }
    }

    return files.map(f => finalResultsMap[f.id]);
};

// --- SINGLE FILE ANALYZER ---
export const fetchTagsForFile = async (
    file: AudioFile,
    provider: AIProvider,
    apiKeys: ApiKeys
): Promise<ID3Tags> => {
    // Wrap in batch for consistent logic
    const results = await smartBatchAnalyze([file], provider, apiKeys, false);
    return results[0] || file.originalTags;
};

// --- SMART PLAYLIST GENERATION (THINKING MODE) ---
export const generateSmartPlaylist = async (
    files: AudioFile[],
    userPrompt: string
): Promise<{ name: string; ids: string[] }> => {
    if (!process.env.API_KEY) throw new Error("Brak klucza API Gemini.");

    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

    const libraryContext = files.map(f => {
        const t = f.fetchedTags || f.originalTags;
        return {
            id: f.id,
            artist: t.artist || 'Unknown',
            title: t.title || f.file.name,
            genre: t.genre,
            bpm: t.bpm,
            mood: t.mood,
            energy: t.energy,
            key: t.initialKey
        };
    }).slice(0, 4000);

    const prompt = `
    You are a professional DJ.
    USER REQUEST: "${userPrompt}"
    LIBRARY: ${JSON.stringify(libraryContext)}
    Create a coherent playlist. Return JSON: { "playlistName": "string", "trackIds": ["id1", "id2"] }
    `;

    try {
        const response = await callGeminiWithRetry(() => 
            ai.models.generateContent({
                model: 'gemini-3-pro-preview',
                contents: prompt,
                config: {
                    thinkingConfig: { thinkingBudget: 32768 },
                    responseMimeType: "application/json",
                }
            })
        );

        const text = response.text || "{}";
        const result = JSON.parse(text);
        
        return {
            name: result.playlistName || "Smart Playlist",
            ids: result.trackIds || []
        };

    } catch (error: any) {
        console.error("Smart Playlist Error:", error);
        throw new Error("AI nie mogło wygenerować playlisty.");
    }
};

// --- IMAGE GENERATION ---
export const generateCoverArt = async (prompt: string, size: '1K' | '2K'): Promise<string> => {
    if (!process.env.API_KEY) throw new Error("Brak klucza API Gemini.");
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-3-pro-image-preview',
            contents: { parts: [{ text: prompt }] },
            config: { imageConfig: { aspectRatio: "1:1", imageSize: size } },
        });
        if (response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data) {
            return `data:image/png;base64,${response.candidates[0].content.parts[0].inlineData.data}`;
        }
        throw new Error("No image returned");
    } catch (error: any) {
        throw new Error(error.message || "Image gen failed");
    }
};
