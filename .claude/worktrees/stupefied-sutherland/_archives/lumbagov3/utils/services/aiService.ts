
import { GoogleGenAI, Type, GenerateContentResponse } from "@google/genai";
import { AudioFile, ID3Tags } from '../../types';

export type AIProvider = 'gemini' | 'grok' | 'openai';

export interface ApiKeys {
  grok: string;
  openai: string;
}

const getSystemInstruction = () => {
  return `You are an expert music archivist equipped with Google Search.
Your task is to identify the song from the provided filename/metadata and return ACCURATE ID3 tags.

**CRITICAL: USE GOOGLE SEARCH** to verify:
1. Exact official Track Title and Artist spelling.
2. Correct Album name (prioritize Original Mix / Single / EP / Album correctly).
3. Release Year.
4. BPM and Key (Camelot notation if possible, e.g. 8A, 11B).
5. Record Label (for Copyright).

RULES:
- If existing tags are correct, keep them.
- If missing/wrong, correct them using search results.
- Do NOT hallucinate. If unsure, return null for that field.
- For 'bpm' return a number (integer).
- For 'initialKey' return the key (e.g. "C min", "11B").

The response must be in JSON format.`;
};

const singleFileResponseSchema = {
    type: Type.OBJECT,
    properties: {
        artist: { type: Type.STRING, description: "The name of the main artist or band." },
        title: { type: Type.STRING, description: "The official title of the song." },
        album: { type: Type.STRING, description: "The name of the album/single/EP." },
        year: { type: Type.STRING, description: "The 4-digit release year." },
        genre: { type: Type.STRING, description: "The primary genre." },
        trackNumber: { type: Type.STRING, description: "Track number." },
        albumArtist: { type: Type.STRING, description: "Album artist." },
        composer: { type: Type.STRING, description: "Composer(s)." },
        copyright: { type: Type.STRING, description: "Copyright info." },
        encodedBy: { type: Type.STRING, description: "Encoder info." },
        originalArtist: { type: Type.STRING, description: "Original artist if cover." },
        discNumber: { type: Type.STRING, description: "Disc number." },
        albumCoverUrl: { type: Type.STRING, description: "URL to high-quality album art." },
        mood: { type: Type.STRING, description: "Mood of the song." },
        comments: { type: Type.STRING, description: "Short facts." },
        bitrate: { type: Type.NUMBER, description: "Bitrate estimate." },
        sampleRate: { type: Type.NUMBER, description: "Sample rate estimate." },
        bpm: { type: Type.NUMBER, description: "BPM (Beats Per Minute)." },
        initialKey: { type: Type.STRING, description: "Musical Key (e.g. 8A, Am)." },
    },
};

const batchFileResponseSchema = {
    type: Type.ARRAY,
    description: "Array of identified tracks.",
    items: {
        type: Type.OBJECT,
        properties: {
            originalFilename: { type: Type.STRING, description: "Filename from prompt." },
            ...singleFileResponseSchema.properties
        },
        required: ["originalFilename"],
    }
};

const callGeminiWithRetry = async (
    apiCall: () => Promise<GenerateContentResponse>,
    maxRetries = 3
): Promise<GenerateContentResponse> => {
    let lastError: Error | null = null;
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await apiCall();
        } catch (error) {
            lastError = error as Error;
            console.warn(`Błąd wywołania API Gemini (próba ${i + 1}/${maxRetries}):`, lastError.message);
            if (i < maxRetries - 1) {
                // Exponential backoff
                const delay = Math.pow(2, i) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    throw lastError || new Error("Nie udało się wykonać zapytania do API po wielokrotnych próbach.");
};

const shouldOverwrite = (newValue: any, oldValue: any): boolean => {
    if (newValue === null || newValue === undefined || newValue === '') return false;
    if (typeof newValue === 'string') {
        const lowerNew = newValue.toLowerCase();
        if ((lowerNew.includes('unknown') || lowerNew.includes('undefined')) && oldValue && oldValue.length > 0) {
            return false;
        }
    }
    return true;
};

const prepareTagsForPrompt = (tags: ID3Tags): Partial<ID3Tags> => {
    if (!tags) return {};
    const { albumCoverUrl, ...rest } = tags;
    return rest;
};


export const fetchTagsForFile = async (
  fileName: string,
  originalTags: ID3Tags,
  provider: AIProvider,
  apiKeys: ApiKeys
): Promise<ID3Tags> => {
  if (provider === 'gemini') {
    if (!process.env.API_KEY) {
      throw new Error("Klucz API Gemini nie jest skonfigurowany.");
    }
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    
    const safeTags = prepareTagsForPrompt(originalTags);
    const prompt = `Find metadata for song file: "${fileName}". Existing clues: ${JSON.stringify(safeTags)}.`;
    
    try {
        const response = await callGeminiWithRetry(() => 
            ai.models.generateContent({
                model: "gemini-3-pro-preview", 
                contents: prompt,
                config: {
                    systemInstruction: getSystemInstruction(),
                    responseMimeType: "application/json",
                    responseSchema: singleFileResponseSchema,
                    // Thinking budget helps, but Search Tool is critical for fresh data
                    thinkingConfig: { thinkingBudget: 16384 }, 
                    tools: [{ googleSearch: {} }] // ENABLE SEARCH GROUNDING
                },
            })
        );

        const text = response.text?.trim() || "{}";
        let parsedResponse: Partial<ID3Tags>;

        try {
            parsedResponse = JSON.parse(text);
        } catch (e) {
            throw new Error("Otrzymano nieprawidłowy format JSON z AI.");
        }

        const mergedTags: ID3Tags = { ...originalTags };
        
        Object.keys(parsedResponse).forEach((key) => {
            const typedKey = key as keyof ID3Tags;
            const newValue = parsedResponse[typedKey];
            const oldValue = originalTags[typedKey];

            if (shouldOverwrite(newValue, oldValue)) {
                (mergedTags as any)[typedKey] = newValue;
            }
        });

        // Log grounding metadata if available (for debugging/attribution)
        // console.debug("Grounding:", response.candidates?.[0]?.groundingMetadata);

        return mergedTags;

    } catch (error) {
        console.error("Błąd Gemini:", error);
        if (error instanceof Error) throw new Error(`Błąd Gemini API: ${error.message}`);
        throw new Error("Wystąpił nieznany błąd z Gemini API.");
    }
  }
  return originalTags;
};

export const fetchTagsForBatch = async (
    files: AudioFile[],
    provider: AIProvider,
    apiKeys: ApiKeys
): Promise<({ originalFilename: string } & ID3Tags)[]> => {
    if (provider === 'gemini') {
        if (!process.env.API_KEY) throw new Error("Brak klucza API Gemini.");
        const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

        const allValidatedResults: ({ originalFilename: string } & ID3Tags)[] = [];
        const BATCH_SIZE = 15; 

        for (let i = 0; i < files.length; i += BATCH_SIZE) {
            const batchFiles = files.slice(i, i + BATCH_SIZE);
            
            const fileList = batchFiles.map(f => JSON.stringify({ 
                filename: f.file.name, 
                existingTags: prepareTagsForPrompt(f.originalTags) 
            })).join(',\n');
            
            const prompt = `Batch identify these songs using Google Search. Filenames:\n[${fileList}]\n\nReturn JSON array.`;

            try {
                const response = await callGeminiWithRetry(() =>
                    ai.models.generateContent({
                        model: "gemini-3-pro-preview", 
                        contents: prompt,
                        config: {
                            systemInstruction: getSystemInstruction(),
                            responseMimeType: "application/json",
                            responseSchema: batchFileResponseSchema,
                            thinkingConfig: { thinkingBudget: 16384 },
                            tools: [{ googleSearch: {} }] // ENABLE SEARCH FOR BATCH TOO
                        },
                    })
                );
                
                const text = response.text?.trim() || "[]";
                let parsedResponse: any[];
                try {
                    parsedResponse = JSON.parse(text);
                } catch { continue; }
                
                if (!Array.isArray(parsedResponse)) continue;
                
                const filesMap = new Map(batchFiles.map(f => [f.file.name, f]));
            
                for (const item of parsedResponse) {
                    if (!item.originalFilename) continue;
                    const originalFile = filesMap.get(item.originalFilename);
                    const originalTags = originalFile ? originalFile.originalTags : {};
                    const mergedItem: any = { originalFilename: item.originalFilename };
                    
                    const allKeys = new Set([...Object.keys(item), ...Object.keys(originalTags)]);
                    allKeys.forEach(key => {
                        if (key === 'originalFilename') return;
                        const newVal = item[key];
                        const oldVal = (originalTags as any)[key];
                        if (shouldOverwrite(newVal, oldVal)) mergedItem[key] = newVal;
                        else mergedItem[key] = oldVal;
                    });
                    allValidatedResults.push(mergedItem);
                }

            } catch (error) {
                console.error(`Błąd wsadowy Gemini (${i}-${i+BATCH_SIZE}):`, error);
                if (error instanceof Error) throw new Error(`Błąd wsadowy Gemini API: ${error.message}`);
                throw error;
            }
        }
        return allValidatedResults;
    }
    throw new Error(`Dostawca ${provider} nieobsługiwany.`);
};
