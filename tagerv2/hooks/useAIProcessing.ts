
import { useState, useCallback } from 'react';
import { AudioFile, ProcessingState, AnalysisSettings } from '../types';
import { smartBatchAnalyze, ApiKeys, AIProvider } from '../services/aiService';

export const useAIProcessing = (
    files: AudioFile[],
    updateFile: (id: string, updates: Partial<AudioFile>) => void,
    apiKeys: ApiKeys,
    aiProvider: AIProvider,
    analysisSettings?: AnalysisSettings
) => {
    const [isBatchAnalyzing, setIsBatchAnalyzing] = useState(false);

    // --- Batch Processor (Smart) ---
    const analyzeBatch = useCallback(async (filesToProcess: AudioFile[], forceUpdate: boolean = false) => {
        if (filesToProcess.length === 0 || isBatchAnalyzing) return;
        
        setIsBatchAnalyzing(true);
        const ids = filesToProcess.map(f => f.id);
        
        // Set state to PROCESSING
        ids.forEach(id => updateFile(id, { state: ProcessingState.PROCESSING, errorMessage: undefined }));
        
        try {
            // The smartBatchAnalyze now handles grouping internaly and research via Google Search
            const resultsTags = await smartBatchAnalyze(filesToProcess, aiProvider, apiKeys, forceUpdate, analysisSettings);
            
            filesToProcess.forEach((file, index) => {
                const tagResult = resultsTags[index];
                if (tagResult && (tagResult.title || tagResult.artist)) {
                    // Update state and merge tags
                    // We prefer AI results for enrichment but keep original tags as base
                    updateFile(file.id, { 
                        state: ProcessingState.SUCCESS, 
                        fetchedTags: { 
                            ...file.originalTags, 
                            ...tagResult,
                            // Ensure dataOrigin reflects the AI enrichment
                            dataOrigin: 'ai-inference'
                        } 
                    });
                } else {
                    updateFile(file.id, { 
                        state: ProcessingState.ERROR, 
                        errorMessage: "AI nie zwróciło danych dla tego pliku." 
                    });
                }
            });

        } catch (e: any) {
            console.error("Batch Error:", e);
            const msg = e.message || "Błąd analizy zbiorczej";
            ids.forEach(id => updateFile(id, { 
                state: ProcessingState.ERROR, 
                errorMessage: msg
            }));
        } finally {
            setIsBatchAnalyzing(false);
        }
    }, [isBatchAnalyzing, aiProvider, apiKeys, updateFile, analysisSettings]);

    // Backward compatibility shim for single file queue
    const addToQueue = useCallback((fileIds: string[]) => {
        const filesToProcess = files.filter(f => fileIds.includes(f.id));
        analyzeBatch(filesToProcess);
    }, [files, analyzeBatch]);

    return {
        addToQueue,
        analyzeBatch,
        isBatchAnalyzing
    };
};
