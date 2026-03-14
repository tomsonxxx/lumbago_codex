// Fix: Provide full implementation for the AI service using Gemini API.
import { GoogleGenAI, Type, GenerateContentResponse } from "@google/genai";
import { AudioFile, ID3Tags } from '../types';

export type AIProvider = 'gemini' | 'grok' | 'openai';

export interface ApiKeys {
  grok: string;
  openai: string;
}

const getSystemInstruction = () => {
  return `You are an expert music archivist and DJ assistant with access to a vast database of music information, equivalent to searching across major portals like MusicBrainz, Discogs, Beatport, AllMusic, Spotify, and Apple Music.
Your task is to identify the song from the provided filename and any existing tags, and then provide the most accurate and complete ID3 tag information possible, with a focus on data useful for DJs.
- Analyze the filename and existing tags to identify the track.
- Search for all relevant tags: title, artist, album, release year, genre.
- Crucially, you must provide the track's BPM (beats per minute) and its musical key in Camelot notation (e.g., "11B", "5A").
- Also find: track number, disc number (e.g., '1/2'), album artist, composer, original artist, copyright info, and who it was encoded by.
- Determine the overall 'mood' of the song (e.g., energetic, melancholic, calm, epic).
- Provide brief 'comments' about the song (e.g., "Classic 80s rock anthem with a memorable guitar solo.").
- VERY IMPORTANT: Prioritize the original studio album the song was first released on. Avoid 'Greatest Hits' compilations, singles, or re-releases unless it's the only available source.
- Find a URL for a high-quality (at least 500x500 pixels) front cover of the album.
- Infer the typical audio properties for this release, such as 'bitrate' (in kbps, e.g., 320) and 'sampleRate' (in Hz, e.g., 44100).
- If you cannot confidently determine a piece of information, leave the corresponding field empty or null. Do not guess.
The response must be in JSON format.`;
};

const singleFileResponseSchema = {
    type: Type.OBJECT,
    properties: {
        artist: { type: Type.STRING, description: "The name of the main artist or band for the track." },
        title: { type: Type.STRING, description: "The official title of the song." },
        album: { type: Type.STRING, description: "The name of the original studio album." },
        year: { type: Type.STRING, description: "The 4-digit release year of the original album or song." },
        genre: { type: Type.STRING, description: "The primary genre of the music." },
        bpm: { type: Type.NUMBER, description: "The beats per minute (BPM) of the track." },
        key: { type: Type.STRING, description: "The musical key of the track in Camelot wheel notation (e.g., '5A', '11B')." },
        trackNumber: { type: Type.STRING, description: "The track number, possibly including the total count (e.g., '01' or '1/12')." },
        albumArtist: { type: Type.STRING, description: "The primary artist for the entire album, if different from the track artist." },
        composer: { type: Type.STRING, description: "The composer(s) of the music." },
        copyright: { type: Type.STRING, description: "Copyright information for the track." },
        encodedBy: { type: Type.STRING, description: "The person or company that encoded the file." },
        originalArtist: { type: Type.STRING, description: "The original artist(s) if the track is a cover." },
        discNumber: { type: Type.STRING, description: "The disc number, possibly including the total count (e.g., '1' or '1/2')." },
        albumCoverUrl: { type: Type.STRING, description: "A direct URL to a high-quality album cover image." },
        mood: { type: Type.STRING, description: "The overall mood or feeling of the song." },
        comments: { type: Type.STRING, description: "Brief interesting facts or description about the song." },
        bitrate: { type: Type.NUMBER, description: "The typical bitrate in kbps for the release (e.g., 320)." },
        sampleRate: { type: Type.NUMBER, description: "The typical sample rate in Hz for the release (e.g., 44100)." },
    },
};

const batchFileResponseSchema = {
    type: Type.ARRAY,
    description: "An array of objects, each containing the tags for a single song from the input list.",
    items: {
        type: Type.OBJECT,
        properties: {
            originalFilename: { type: Type.STRING, description: "The original filename provided in the prompt, used for mapping the results back." },
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
                console.log(`Ponawiam próbę za ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    throw lastError || new Error("Nie udało się wykonać zapytania do API po wielokrotnych próbach.");
};


export const fetchTagsForFile = async (
  fileName: string,
  originalTags: ID3Tags,
  provider: AIProvider,
  apiKeys: ApiKeys
): Promise<ID3Tags> => {
  if (provider === 'gemini') {
    if (!process.env.API_KEY) {
      throw new Error("Klucz API Gemini nie jest skonfigurowany w zmiennych środowiskowych (API_KEY).");
    }
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    
    const prompt = `Identify this song and provide its tags. Filename: "${fileName}". Existing tags: ${JSON.stringify(originalTags)}.`;
    
    try {
        const response = await callGeminiWithRetry(() => 
            ai.models.generateContent({
                model: "gemini-2.5-flash",
                contents: prompt,
                config: {
                    systemInstruction: getSystemInstruction(),
                    responseMimeType: "application/json",
                    responseSchema: singleFileResponseSchema,
                },
            })
        );

        const text = response.text.trim();
        let parsedResponse: Partial<ID3Tags>;

        try {
            parsedResponse = JSON.parse(text);
        } catch (e) {
            console.error("Nie udało się sparsować JSON z Gemini:", text);
            throw new Error("Otrzymano nieprawidłowy format JSON z AI.");
        }

        const mergedTags: ID3Tags = {
            ...originalTags,
            ...parsedResponse
        };

        Object.keys(mergedTags).forEach(key => {
            const typedKey = key as keyof ID3Tags;
            if (mergedTags[typedKey] === "" || mergedTags[typedKey] === null) {
                delete mergedTags[typedKey];
            }
        });

        return mergedTags;

    } catch (error) {
        console.error("Błąd podczas pobierania tagów z Gemini API:", error);
        if (error instanceof Error) {
           throw new Error(`Błąd Gemini API: ${error.message}`);
        }
        throw new Error("Wystąpił nieznany błąd z Gemini API.");
    }
  }
  
  // Handle other providers
  if (provider === 'grok') {
    if (!apiKeys.grok) {
      throw new Error("Klucz API dla Grok nie został podany w ustawieniach.");
    }
    // Placeholder for actual Grok API call
    console.warn(`Dostawca Grok nie jest jeszcze zaimplementowany. Użycie klucza API zostało pominięte.`);
    return originalTags;
  }

  if (provider === 'openai') {
    if (!apiKeys.openai) {
      throw new Error("Klucz API dla OpenAI nie został podany w ustawieniach.");
    }
    // Placeholder for actual OpenAI API call
    console.warn(`Dostawca OpenAI nie jest jeszcze zaimplementowany. Użycie klucza API zostało pominięte.`);
    return originalTags;
  }
  
  // Fallback for an unknown provider
  console.warn(`Nieznany dostawca ${provider}. Zwracam oryginalne tagi.`);
  return originalTags;
};

export interface BatchResult extends ID3Tags {
    originalFilename: string;
}

export const fetchTagsForBatch = async (
    files: AudioFile[],
    provider: AIProvider,
    apiKeys: ApiKeys
): Promise<BatchResult[]> => {
    if (provider === 'gemini') {
        if (!process.env.API_KEY) {
            throw new Error("Klucz API Gemini nie jest skonfigurowany w zmiennych środowiskowych (API_KEY).");
        }
        const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

        const fileList = files.map(f => JSON.stringify({ filename: f.file.name, existingTags: f.originalTags })).join(',\n');
        const prompt = `You are a music archivist. I have a batch of audio files that may be from the same album or artist. Please identify each track based on its filename and existing tags, and provide its full ID3 tags. Pay close attention to filenames that suggest they are from the same album or artist (e.g., sequential track numbers like '01-song.mp3', '02-another.mp3'). For these related files, ensure the 'artist', 'album', and 'albumArtist' tags are identical to maintain consistency. Here is the list of files:\n\n[${fileList}]\n\nReturn your response as a valid JSON array. Each object in the array must correspond to one of the input files and contain the 'originalFilename' I provided, along with all the identified tags from the schema.`;

        try {
            const response = await callGeminiWithRetry(() =>
                ai.models.generateContent({
                    model: "gemini-2.5-flash",
                    contents: prompt,
                    config: {
                        systemInstruction: getSystemInstruction(),
                        responseMimeType: "application/json",
                        responseSchema: batchFileResponseSchema,
                    },
                })
            );
            
            const text = response.text.trim();
            let parsedResponse: any[];
            try {
                parsedResponse = JSON.parse(text);
            } catch (e) {
                console.error("Failed to parse JSON from Gemini batch response:", text, e);
                throw new Error("Otrzymano nieprawidłowy format JSON z AI.");
            }
            
            if (!Array.isArray(parsedResponse)) {
                 console.error("Batch AI response is not a valid JSON array.", parsedResponse);
                 throw new Error("Odpowiedź AI nie jest w formacie tablicy JSON.");
            }
            
            const validatedResults: BatchResult[] = [];
            const requestedFilenames = new Set(files.map(f => f.file.name));
            const processedFilenames = new Set<string>();
        
            for (const item of parsedResponse) {
                try {
                    if (typeof item !== 'object' || item === null) {
                        console.warn("Skipping invalid item in batch response (not an object):", item);
                        continue;
                    }
                    if (!item.originalFilename || typeof item.originalFilename !== 'string') {
                        console.warn("Skipping item in batch response with missing or invalid 'originalFilename':", item);
                        continue;
                    }
                    if (processedFilenames.has(item.originalFilename)) {
                        console.warn(`Skipping duplicate entry in batch response for filename: ${item.originalFilename}`);
                        continue;
                    }
                    if (!requestedFilenames.has(item.originalFilename)) {
                        console.warn(`Skipping item in batch response with an unexpected 'originalFilename' that was not in the request: ${item.originalFilename}`);
                        continue;
                    }
                    validatedResults.push(item as BatchResult);
                    processedFilenames.add(item.originalFilename);
                } catch (e) {
                    console.error("Error processing a single item in batch response. Skipping.", { item, error: e });
                }
            }
        
            if(validatedResults.length < files.length) {
                console.warn(`Batch response contained ${validatedResults.length} valid items, but ${files.length} files were requested. Some files may not be updated.`);
            }
            
            return validatedResults;

        } catch (error) {
            console.error("Błąd podczas pobierania tagów wsadowo z Gemini API:", error);
            if (error instanceof Error) {
               throw new Error(`Błąd wsadowy Gemini API: ${error.message}`);
            }
            throw new Error("Wystąpił nieznany błąd wsadowy z Gemini API.");
        }
    }

    // Handle other providers for batch mode
    if (provider === 'grok') {
        if (!apiKeys.grok) {
          throw new Error("Klucz API dla Grok nie został podany w ustawieniach.");
        }
        throw new Error("Tryb wsadowy nie jest zaimplementowany dla dostawcy Grok.");
    }

    if (provider === 'openai') {
        if (!apiKeys.openai) {
          throw new Error("Klucz API dla OpenAI nie został podany w ustawieniach.");
        }
        throw new Error("Tryb wsadowy nie jest zaimplementowany dla dostawcy OpenAI.");
    }

    throw new Error(`Nieznany dostawca ${provider} nie jest obsługiwany w trybie wsadowym.`);
};