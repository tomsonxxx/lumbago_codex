
import React, { useState } from 'react';
import { GoogleGenAI } from "@google/genai";

export const SmartTaggerAI = () => {
    const [prompt, setPrompt] = useState('');
    const [result, setResult] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const generateTags = async () => {
        if (!prompt) return;
        setIsLoading(true);
        setError('');
        setResult('');

        try {
            const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
            const response = await ai.models.generateContent({
                model: 'gemini-3-pro-preview',
                contents: `Jako ekspert muzyczny i DJ, przeanalizuj ten opis utworu i wygeneruj profesjonalne tagi.
                Opis: "${prompt}"
                
                Proszę o odpowiedź w formacie:
                Gatunek: [Gatunek]
                Nastrój: [Nastrój]
                BPM (Sugestia): [BPM]
                Klucz (Sugestia): [Klucz]
                Podobni Artyści: [Lista]
                Opis: [Krótkie podsumowanie]`,
                config: {
                    thinkingConfig: { thinkingBudget: 32768 }
                }
            });

            if (response.text) {
                setResult(response.text);
            }
        } catch (err: any) {
            setError('Błąd generowania: ' + (err.message || 'Nieznany błąd'));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <textarea 
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                placeholder="Wpisz opis utworu (np. 'Szybki kawałek techno z mocnym basem i wokalem żeńskim w klimacie lat 90.')"
                className="w-full h-32 bg-gray-800 border border-gray-700 rounded p-4 text-gray-100"
            />
            <button onClick={generateTags} disabled={isLoading} className="px-6 py-2 bg-purple-600 hover:bg-purple-500 rounded font-bold w-full disabled:opacity-50">
                {isLoading ? 'Analizowanie (AI Thinking)...' : 'Generuj Tagi AI'}
            </button>
            {error && <div className="text-red-400">{error}</div>}
            {result && (
                <div className="bg-gray-800 p-6 rounded border border-gray-700 whitespace-pre-line">
                    {result}
                </div>
            )}
        </div>
    );
};
