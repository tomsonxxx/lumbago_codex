import { GoogleGenAI, Type } from '@google/genai';
import { ID3Tags } from '../types';

export type AIProvider = 'gemini' | 'grok' | 'openai';

export interface ApiKeys {
  grok: string;
  openai: string;
}

export interface ProviderAnalysisResult {
  provider: AIProvider;
  model: string;
  tags: Partial<ID3Tags>;
  confidence: number;
  error?: string;
}

const PROVIDER_MODELS: Record<AIProvider, string> = {
  gemini: 'gemini-2.5-flash',
  openai: 'gpt-4.1-mini',
  grok: 'grok-2-latest',
};

const SYSTEM_PROMPT = `You are a meticulous DJ metadata expert.
Return ONLY JSON with best effort metadata for an audio track.
You must infer fields: title, artist, album, year, genre, bpm, key, trackNumber, discNumber, albumArtist, composer, comments, mood.
Return confidence 0..1 (global) and optional fieldConfidence object with 0..1 per field.
Do not include markdown fences.`;

const RESPONSE_SCHEMA = {
  type: Type.OBJECT,
  properties: {
    title: { type: Type.STRING },
    artist: { type: Type.STRING },
    album: { type: Type.STRING },
    year: { type: Type.STRING },
    genre: { type: Type.STRING },
    bpm: { type: Type.NUMBER },
    key: { type: Type.STRING },
    trackNumber: { type: Type.STRING },
    discNumber: { type: Type.STRING },
    albumArtist: { type: Type.STRING },
    composer: { type: Type.STRING },
    comments: { type: Type.STRING },
    mood: { type: Type.STRING },
    confidence: { type: Type.NUMBER },
    fieldConfidence: { type: Type.OBJECT },
  },
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const parseJsonSafe = (payload: string): Record<string, any> => {
  const trimmed = payload.trim().replace(/^```json/i, '').replace(/^```/, '').replace(/```$/, '');
  return JSON.parse(trimmed);
};

const normalizeTags = (raw: Record<string, any>): Partial<ID3Tags> => {
  const out: Partial<ID3Tags> = {};
  const keys: (keyof ID3Tags)[] = [
    'title',
    'artist',
    'album',
    'year',
    'genre',
    'trackNumber',
    'discNumber',
    'albumArtist',
    'composer',
    'comments',
    'mood',
    'bpm',
    'key',
    'albumCoverUrl',
  ];

  for (const key of keys) {
    const value = raw[key as string];
    if (value === null || value === undefined || value === '') {
      continue;
    }
    if (key === 'bpm') {
      const bpm = Number(value);
      if (Number.isFinite(bpm) && bpm >= 40 && bpm <= 260) {
        out.bpm = Number(bpm.toFixed(1));
      }
      continue;
    }
    if (key === 'year') {
      const year = String(value).match(/\d{4}/)?.[0];
      if (year) {
        out.year = year;
      }
      continue;
    }
    if (key === 'key') {
      const normalizedKey = String(value).trim();
      if (/^(1[0-2]|[1-9])[AB]$/i.test(normalizedKey) || /^[A-G](#|b)?m?$/i.test(normalizedKey)) {
        out.key = normalizedKey;
      }
      continue;
    }
    (out as any)[key] = String(value).trim();
  }
  return out;
};

const callGemini = async (prompt: string): Promise<{ payload: Record<string, any>; model: string }> => {
  if (!process.env.API_KEY) {
    throw new Error('Brak API_KEY dla Gemini.');
  }
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  let lastError: unknown;
  for (let i = 0; i < 3; i++) {
    try {
      const response = await ai.models.generateContent({
        model: PROVIDER_MODELS.gemini,
        contents: prompt,
        config: {
          systemInstruction: SYSTEM_PROMPT,
          responseMimeType: 'application/json',
          responseSchema: RESPONSE_SCHEMA,
        },
      });
      return { payload: parseJsonSafe(response.text), model: PROVIDER_MODELS.gemini };
    } catch (error) {
      lastError = error;
      await sleep(500 * (i + 1));
    }
  }
  throw lastError instanceof Error ? lastError : new Error('Gemini failed');
};

const callChatCompletions = async (
  provider: 'openai' | 'grok',
  apiKey: string,
  prompt: string
): Promise<{ payload: Record<string, any>; model: string }> => {
  const endpoint = provider === 'openai' ? 'https://api.openai.com/v1/chat/completions' : 'https://api.x.ai/v1/chat/completions';
  const model = PROVIDER_MODELS[provider];
  let lastError: unknown;

  for (let i = 0; i < 2; i++) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model,
          temperature: 0.2,
          response_format: { type: 'json_object' },
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: prompt },
          ],
        }),
      });
      if (!response.ok) {
        throw new Error(`${provider} HTTP ${response.status}`);
      }
      const data = await response.json();
      const content = data?.choices?.[0]?.message?.content ?? '{}';
      return { payload: parseJsonSafe(content), model };
    } catch (error) {
      lastError = error;
      await sleep(500 * (i + 1));
    }
  }
  throw lastError instanceof Error ? lastError : new Error(`${provider} failed`);
};

export const analyzeWithProviders = async (
  prompt: string,
  apiKeys: ApiKeys
): Promise<ProviderAnalysisResult[]> => {
  const tasks: Promise<ProviderAnalysisResult>[] = [];

  tasks.push(
    callGemini(prompt)
      .then(({ payload, model }) => ({
        provider: 'gemini' as const,
        model,
        tags: normalizeTags(payload),
        confidence: Math.max(0, Math.min(1, Number(payload.confidence ?? 0.72))),
      }))
      .catch((error: unknown) => ({
        provider: 'gemini' as const,
        model: PROVIDER_MODELS.gemini,
        tags: {},
        confidence: 0,
        error: error instanceof Error ? error.message : 'Gemini error',
      }))
  );

  if (apiKeys.openai) {
    tasks.push(
      callChatCompletions('openai', apiKeys.openai, prompt)
        .then(({ payload, model }) => ({
          provider: 'openai' as const,
          model,
          tags: normalizeTags(payload),
          confidence: Math.max(0, Math.min(1, Number(payload.confidence ?? 0.68))),
        }))
        .catch((error: unknown) => ({
          provider: 'openai' as const,
          model: PROVIDER_MODELS.openai,
          tags: {},
          confidence: 0,
          error: error instanceof Error ? error.message : 'OpenAI error',
        }))
    );
  }

  if (apiKeys.grok) {
    tasks.push(
      callChatCompletions('grok', apiKeys.grok, prompt)
        .then(({ payload, model }) => ({
          provider: 'grok' as const,
          model,
          tags: normalizeTags(payload),
          confidence: Math.max(0, Math.min(1, Number(payload.confidence ?? 0.65))),
        }))
        .catch((error: unknown) => ({
          provider: 'grok' as const,
          model: PROVIDER_MODELS.grok,
          tags: {},
          confidence: 0,
          error: error instanceof Error ? error.message : 'Grok error',
        }))
    );
  }

  return Promise.all(tasks);
};
