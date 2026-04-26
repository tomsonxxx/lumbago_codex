import React, { useState, useEffect } from "react";
import { AudioFile, ID3Tags } from "../types";
import { fetchTagsForFile } from "../services/aiService";
import { useSettings } from "../hooks/useSettings";

interface SmartTaggerModalProps {
  isOpen: boolean;
  onClose: () => void;
  file: AudioFile;
  onApply: (tags: ID3Tags) => void;
}

const SmartTaggerModal: React.FC<SmartTaggerModalProps> = ({
  isOpen,
  onClose,
  file,
  onApply,
}) => {
  const { aiProvider, apiKeys } = useSettings();
  const [analyzedTags, setAnalyzedTags] = useState<ID3Tags | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && file && !analyzedTags && !isProcessing) {
      handleAnalyze();
    }
  }, [isOpen, file]);

  const handleAnalyze = async () => {
    setIsProcessing(true);
    setError(null);
    try {
      const gKeys = { grok: apiKeys.grok, openai: apiKeys.openai };
      const tags = await fetchTagsForFile(file, aiProvider, gKeys);
      setAnalyzedTags(tags);
    } catch (err: any) {
      setError(err.message || "Błąd analizy AI");
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  const currentTags = file.fetchedTags || file.originalTags;

  const TagComparison = ({
    label,
    current,
    suggested,
  }: {
    label: string;
    current: any;
    suggested: any;
  }) => {
    const isDifferent = suggested !== undefined && suggested !== current;
    return (
      <div className="flex flex-col py-2 border-b border-[#333] last:border-0">
        <span className="text-[9px] font-mono font-bold text-[var(--text-muted)] tracking-widest">
          {label}
        </span>
        <div className="flex items-center justify-between mt-1">
          <div className="flex-1 font-mono text-[10px]">
            <span className="text-[#666] line-through mr-3">
              {current || "---"}
            </span>
            <span
              className={`font-bold ${isDifferent ? "text-[var(--accent-primary)]" : "text-[var(--text-primary)]"}`}
            >
              {suggested || current || "---"}
            </span>
          </div>
          {isDifferent && (
            <div className="w-1.5 h-1.5 bg-[var(--accent-primary)] shadow-[0_0_5px_var(--accent-primary)]"></div>
          )}
        </div>
      </div>
    );
  };  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="glass-panel w-full max-w-xl p-8 rounded-[2.5rem] border border-white/10 shadow-2xl relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--accent-cyan)]/10 blur-3xl rounded-full -mr-16 -mt-16"></div>
        
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
             <div className="p-3 bg-[var(--accent-magenta)] rounded-2xl glow-magenta text-white">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
             </div>
             <div>
               <h2 className="text-xl font-bold text-white font-heading tracking-tight">AI Smart Tagger</h2>
               <p className="text-[10px] text-white/30 uppercase font-black tracking-widest">Neural Analysis Engine</p>
             </div>
          </div>
          <button onClick={onClose} className="p-2 text-white/20 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-6 p-4 bg-white/5 rounded-2xl border border-white/5">
           <div className="text-[10px] text-white/30 uppercase font-black tracking-widest mb-1">Target File</div>
           <div className="text-xs text-white font-mono truncate">{file.file.name}</div>
        </div>

        <div className="space-y-4">
          {isProcessing ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-6">
              <div className="w-16 h-16 border-4 border-[var(--accent-cyan)]/20 border-t-[var(--accent-cyan)] rounded-full animate-spin glow-cyan"></div>
              <div className="text-[10px] font-black text-[var(--accent-cyan)] uppercase tracking-[0.3em] animate-pulse">Scanning Audio Vectors...</div>
            </div>
          ) : error ? (
            <div className="p-6 bg-[var(--accent-magenta)]/5 border border-[var(--accent-magenta)]/20 rounded-2xl flex items-center gap-4">
               <div className="p-2 bg-[var(--accent-magenta)]/20 rounded-lg text-[var(--accent-magenta)]">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
               </div>
               <div className="flex-grow">
                  <div className="text-sm font-bold text-white">Błąd Analizy</div>
                  <div className="text-xs text-white/40">{error}</div>
               </div>
               <button onClick={handleAnalyze} className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-[10px] font-bold text-white uppercase tracking-widest transition-all">Ponów</button>
            </div>
          ) : analyzedTags ? (
            <div className="bg-white/5 border border-white/5 rounded-3xl p-6 space-y-2">
              <TagComparison label="ARTYSTA" current={currentTags.artist} suggested={analyzedTags.artist} />
              <TagComparison label="TYTUŁ" current={currentTags.title} suggested={analyzedTags.title} />
              <TagComparison label="GATUNEK" current={currentTags.genre} suggested={analyzedTags.genre} />
              <TagComparison label="BPM" current={currentTags.bpm} suggested={analyzedTags.bpm} />
              <TagComparison label="TONACJA" current={currentTags.initialKey} suggested={analyzedTags.initialKey} />
              
              <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-[8px] font-black uppercase tracking-[0.2em] text-white/20">
                <span>Źródło: {analyzedTags.dataOrigin || "AI_ENGINE"}</span>
                <span>Pewność: {analyzedTags.comment?.includes("confidence") ? "Wysoka" : "Normalna"}</span>
              </div>
            </div>
          ) : null}

          <div className="flex gap-4 mt-8">
            <button onClick={onClose} className="flex-1 px-6 py-4 text-xs font-bold text-white/30 hover:text-white uppercase tracking-widest transition-colors">ANULUJ</button>
            <button
              disabled={!analyzedTags || isProcessing}
              onClick={() => analyzedTags && onApply(analyzedTags)}
              className="flex-[2] px-8 py-4 bg-[var(--accent-cyan)] text-black text-xs font-bold rounded-2xl glow-cyan hover:scale-[1.02] active:scale-95 disabled:opacity-20 disabled:scale-100 transition-all uppercase tracking-widest"
            >
              ZASTOSUJ TAGI
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SmartTaggerModal;
