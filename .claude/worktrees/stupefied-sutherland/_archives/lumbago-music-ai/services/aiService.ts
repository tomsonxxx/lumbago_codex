
import { GoogleGenAI, GenerateContentResponse } from "@google/genai";
import { AudioFile, ID3Tags, AnalysisSettings } from '../types';
import { getCachedAnalysis, cacheAnalysisResult } from './cacheService';

export type AIProvider = 'gemini' | 'grok' | 'openai';

export interface ApiKeys {
  grok: string;
  openai: string;
}

// --- SYSTEM INSTRUCTIONS ---
const getSystemInstruction = (settings?: AnalysisSettings) => {
  return `You are "Lumbago Supervisor", an elite music archivist and DJ librarian AI.
Your goal is to repair, organize, and enrich metadata for music files with professional accuracy.

RULES:
- Use Google Search to verify release dates, labels, and genres.
- Return pure JSON Array.
- confidence: 'high' only if verified online.
- Do not hallucinate fields.
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
            if (error.status === 400 || error.status === 401 || error.status === 403) throw error;
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
    settings?: AnalysisSettings
): Promise<ID3Tags[]> => {
    if (!process.env.API_KEY) throw new Error("Missing Gemini API_KEY.");

    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
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

    const prompt = `Analyze these music files. Return JSON array. 
    Files: ${filesToFetch.map(f => f.file.name).join(', ')}`;

    try {
        const response = await callGeminiWithRetry(() => 
            ai.models.generateContent({
                model: "gemini-2.5-flash",
                contents: prompt,
                config: {
                    systemInstruction: getSystemInstruction(settings),
                    tools: [{ googleSearch: {} }],
                    responseMimeType: "application/json"
                }
            })
        );
        
        const text = response.text || "[]";
        let parsed = [];
        try {
             parsed = JSON.parse(text);
        } catch (e) {
             console.error("JSON Parse Error", text);
        }
        
        filesToFetch.forEach((f, i) => {
            const res = parsed[i] || {};
            const tag: ID3Tags = { ...f.originalTags, ...res, dataOrigin: 'ai-inference' };
            cacheAnalysisResult(f.file, tag);
            finalResultsMap[f.id] = tag;
        });

    } catch (e) {
        console.error("Batch failed", e);
        filesToFetch.forEach(f => finalResultsMap[f.id] = f.originalTags);
    }

    return files.map(f => finalResultsMap[f.id]);
};

// --- SINGLE FILE ANALYZER ---
export const fetchTagsForFile = async (
    file: AudioFile,
    provider: AIProvider,
    apiKeys: ApiKeys,
    settings?: AnalysisSettings
): Promise<ID3Tags> => {
    // Wrap in batch for consistent logic
    const results = await smartBatchAnalyze([file], provider, apiKeys, false, settings);
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
