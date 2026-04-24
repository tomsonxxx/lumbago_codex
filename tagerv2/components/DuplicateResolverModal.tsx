import React, { useState, useMemo } from "react";
import { AudioFile } from "../types";

interface DuplicateResolverModalProps {
  isOpen: boolean;
  onClose: () => void;
  duplicateSets: Map<string, AudioFile[]>;
  onRemoveFiles: (fileIds: string[]) => void;
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const DuplicateResolverModal: React.FC<DuplicateResolverModalProps> = ({
  isOpen,
  onClose,
  duplicateSets,
  onRemoveFiles,
}) => {
  const [selectedForDeletion, setSelectedForDeletion] = useState<Set<string>>(
    new Set(),
  );
  const sets = useMemo(
    () => Array.from(duplicateSets.entries()),
    [duplicateSets],
  );

  const toggleSelection = (id: string) => {
    const newSet = new Set(selectedForDeletion);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedForDeletion(newSet);
  };

  const handleAutoSelect = () => {
    const newSelection = new Set<string>();
    sets.forEach(([, files]) => {
      // Sort by quality (bitrate/size) - keep the best one
      const sorted = [...files].sort((a, b) => {
        const bitrateA = a.fetchedTags?.bitrate || a.originalTags?.bitrate || 0;
        const bitrateB = b.fetchedTags?.bitrate || b.originalTags?.bitrate || 0;
        if (bitrateB !== bitrateA) return bitrateB - bitrateA;
        return b.file.size - a.file.size;
      });
      // Mark all except the first (best) for deletion
      for (let i = 1; i < sorted.length; i++) newSelection.add(sorted[i].id);
    });
    setSelectedForDeletion(newSelection);
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="glass-panel flex flex-col w-full max-w-5xl h-[85vh] rounded-[2.5rem] border border-white/10 overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-8 border-b border-white/5 flex justify-between items-center bg-black/20">
          <div>
            <h2 className="text-2xl font-bold text-white font-heading">
               Duplikaty
            </h2>
            <p className="text-xs text-white/30 uppercase font-bold tracking-widest mt-1">
               Znaleziono {sets.length} grup potencjalnych duplikatów
            </p>
          </div>
          <button
            onClick={handleAutoSelect}
            className="px-6 py-3 bg-[var(--accent-magenta)]/10 text-[var(--accent-magenta)] border border-[var(--accent-magenta)]/20 rounded-2xl text-[10px] uppercase font-black tracking-widest hover:bg-[var(--accent-magenta)] hover:text-white transition-all glow-magenta"
          >
            Auto-zaznacz (Gorsza Jakość)
          </button>
        </div>

        <div className="flex-grow overflow-y-auto p-8 space-y-8 scrollbar-hide">
          {sets.map(([setId, files]) => (
            <div
              key={setId}
              className="bg-white/5 rounded-[2rem] border border-white/5 overflow-hidden"
            >
              <div className="bg-white/5 px-6 py-3 text-[10px] font-black text-white/30 uppercase tracking-[0.2em] border-b border-white/5 flex justify-between">
                <span>Grupa {setId.slice(0, 8)}</span>
                <span className="text-[var(--accent-cyan)]">{files.length} PLIKI</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <tbody>
                    {files.map((file) => {
                      const isMarked = selectedForDeletion.has(file.id);
                      const bitrate = file.fetchedTags?.bitrate || file.originalTags?.bitrate;
                      return (
                        <tr
                          key={file.id}
                          className={`group transition-all ${isMarked ? "bg-[var(--accent-magenta)]/5" : "hover:bg-white/5"}`}
                        >
                          <td className="px-6 py-4 w-12">
                             <div 
                                onClick={() => toggleSelection(file.id)}
                                className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center cursor-pointer transition-all ${isMarked ? "bg-[var(--accent-magenta)] border-[var(--accent-magenta)] glow-magenta" : "border-white/10 hover:border-white/30"}`}
                             >
                               {isMarked && (
                                 <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" viewBox="0 0 20 20" fill="currentColor">
                                   <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                 </svg>
                               )}
                             </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className={`text-sm font-bold ${isMarked ? "text-white/20 line-through" : "text-white"}`}>
                              {file.file.name}
                            </div>
                            <div className="text-[10px] text-white/20 font-mono mt-1 line-clamp-1">{file.webkitRelativePath}</div>
                          </td>
                          <td className="px-6 py-4 text-right">
                             <div className="text-xs font-bold text-[var(--accent-cyan)]">{bitrate ? `${Math.round(bitrate / 1000)} kbps` : "—"}</div>
                             <div className="text-[10px] text-white/30 font-mono">{formatSize(file.file.size)}</div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>

        <div className="p-8 border-t border-white/5 bg-black/20 flex justify-between items-center">
          <div className="text-xs font-bold tracking-widest text-white/40">
            ZAZNACZONE: <span className={selectedForDeletion.size > 0 ? "text-[var(--accent-magenta)] glow-magenta" : ""}>{selectedForDeletion.size} PLIKÓW</span>
          </div>
          <div className="flex gap-4">
            <button
              onClick={onClose}
              className="px-6 py-3 text-xs font-bold text-white/30 hover:text-white uppercase tracking-widest transition-colors"
            >
              Anuluj
            </button>
            <button
              onClick={() => {
                onRemoveFiles(Array.from(selectedForDeletion));
                onClose();
              }}
              disabled={selectedForDeletion.size === 0}
              className="px-8 py-4 bg-[var(--accent-magenta)] text-white text-xs font-bold rounded-2xl glow-magenta hover:scale-105 active:scale-95 disabled:opacity-20 disabled:scale-100 transition-all uppercase tracking-widest"
            >
              Usuń zaznaczone
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DuplicateResolverModal;
