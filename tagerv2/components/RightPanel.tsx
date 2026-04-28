import React from "react";
import { AudioFile } from "../types";
import AlbumCover from "./AlbumCover";

interface RightPanelProps {
  file: AudioFile | null;
  allFiles: AudioFile[];
  onClose: () => void;
  onRenamePatternSettings: () => void;
  onActivateFile?: (file: AudioFile) => void;
  filters?: any;
  onFilterChange?: (filters: any) => void;
  availableGenres?: string[];
  popularTags?: string[];
}


const DetailRow: React.FC<{
  label: string;
  value: string | number | undefined;
}> = ({ label, value }) => (
  <div className="py-2 border-b border-[var(--border-color)] last:border-0 flex justify-between items-center group hover:bg-[#111] px-1 transition-colors">
    <dt className="text-[9px] font-mono font-bold text-[var(--text-muted)] tracking-widest">
      {label}
    </dt>
    <dd className="text-[10px] font-mono text-[var(--text-primary)] text-right truncate max-w-[65%]">
      {value || "-"}
    </dd>
  </div>
);


const RightPanel: React.FC<RightPanelProps & { isFilterView?: boolean }> = ({
  file,
  onClose,
  isFilterView,
  filters,
  onFilterChange,
  availableGenres,
  popularTags = []
}) => {
  if (isFilterView) {
    const handleGenreChange = (genre: string | null) => {
      if (onFilterChange) onFilterChange({ ...filters, genre: genre === "Wszystkie" ? undefined : genre });
    };

    return (
      <aside className="w-80 glass-effect border-l border-white/5 flex flex-col h-full z-30 shadow-[-20px_0_40px_rgba(0,0,0,0.5)]">
        <div className="p-6 flex items-center justify-between border-b border-white/5">
          <h2 className="text-xl font-bold text-white font-heading">Filtry</h2>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-lg text-white/40 hover:text-white transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-hide">
          {/* Search in filters */}
          <div className="space-y-3">
             <label className="text-[10px] uppercase tracking-widest text-white/30 font-bold">Wyszukaj</label>
             <div className="relative">
                <input 
                  type="text" 
                  value={filters?.search || ""}
                  onChange={(e) => onFilterChange?.({ ...filters, search: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-10 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent-cyan)]/50 text-white" 
                  placeholder="NP. Techno..."
                />
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
             </div>
          </div>

          <div className="space-y-6">
             <div className="space-y-2">
                <label className="text-[10px] uppercase tracking-widest text-white/30 font-bold">Gatunek</label>
                <select 
                  value={filters?.genre || ""}
                  onChange={(e) => handleGenreChange(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 focus:outline-none text-sm text-white/60 appearance-none"
                >
                  <option value="">Wszystkie</option>
                  {availableGenres?.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
             </div>

             <div className="space-y-2">
                <label className="text-[10px] uppercase tracking-widest text-white/30 font-bold">BPM</label>
                <div className="flex gap-2">
                   <input 
                     type="number" 
                     placeholder="Min" 
                     className="w-1/2 bg-white/5 border border-white/10 rounded-xl py-2 px-3 text-xs" 
                     onChange={(e) => onFilterChange?.({ ...filters, minBpm: parseInt(e.target.value) || undefined })}
                   />
                   <input 
                     type="number" 
                     placeholder="Max" 
                     className="w-1/2 bg-white/5 border border-white/10 rounded-xl py-2 px-3 text-xs"
                     onChange={(e) => onFilterChange?.({ ...filters, maxBpm: parseInt(e.target.value) || undefined })}
                   />
                </div>
             </div>
          </div>

          <div className="space-y-3">
             <label className="text-[10px] uppercase tracking-widest text-white/30 font-bold">TOP 15 Tagi</label>
             <div className="flex flex-wrap gap-2">
                {popularTags.map(tag => (
                   <button 
                     key={tag}
                     onClick={() => onFilterChange?.({ ...filters, search: tag })}
                     className={`px-3 py-1.5 rounded-full border text-[11px] transition-all ${filters?.search === tag ? 'bg-[var(--accent-cyan)] text-black glow-cyan border-transparent' : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/10'}`}
                   >
                     {tag}
                   </button>
                ))}
                {popularTags.length === 0 && <p className="text-[10px] text-white/10 italic">Brak tagów do wyświetlenia</p>}
             </div>
          </div>
        </div>

        <div className="p-6 border-t border-white/5">
           <button 
             onClick={onClose}
             className="w-full py-4 bg-[var(--accent-magenta)] text-white rounded-2xl font-bold shadow-lg glow-magenta hover:scale-[1.02] active:scale-95 transition-all"
            >
              Zastosuj Filtry
           </button>
        </div>
      </aside>
    );
  }

  if (!file) return null;

  const tags = file.fetchedTags || file.originalTags || {};

  return (
    <aside className="w-80 glass-effect border-l border-white/5 flex flex-col h-full z-30">
      <div className="p-6 flex items-center justify-between border-b border-white/5">
        <h2 className="text-xl font-bold text-white font-heading">Szczegóły</h2>
        <button 
          onClick={onClose}
          className="p-2 hover:bg-white/5 rounded-lg text-white/40 hover:text-white transition-all"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
        <div className="w-full aspect-square rounded-2xl overflow-hidden border border-white/10 glow-cyan">
          <AlbumCover tags={tags} className="w-full h-full object-cover" />
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="text-2xl font-bold text-white mb-1">{tags.title || file.file.name}</h3>
            <p className="text-[var(--accent-cyan)] font-semibold tracking-wide uppercase text-xs">{tags.artist || "UNKNOWN ARTIST"}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
             <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
                <p className="text-[10px] text-white/40 font-bold uppercase tracking-widest mb-1">BPM</p>
                <p className="text-2xl font-bold text-white">{tags.bpm || "---"}</p>
             </div>
             <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
                <p className="text-[10px] text-white/40 font-bold uppercase tracking-widest mb-1">Tonacja</p>
                <p className="text-2xl font-bold text-[var(--accent-magenta)]">{tags.initialKey || "--"}</p>
             </div>
          </div>

          <div className="space-y-3">
             <DetailRow label="ALBUM" value={tags.album} />
             <DetailRow label="GATUNEK" value={tags.genre} />
             <DetailRow label="ROK" value={tags.year} />
             <DetailRow label="ETYKIETA" value={(tags as any).label} />
          </div>
        </div>
      </div>
    </aside>
  );
};

export default RightPanel;
