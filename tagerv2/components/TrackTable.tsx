import React, { useState, useCallback, useRef } from "react";
import { AudioFile } from "../types";
import { SortConfig, SortKey } from "../utils/sortingUtils";

interface TrackTableProps {
  files: AudioFile[];
  selectedFileIds: string[];
  activeFileId: string | null;
  onSelect: (id: string, multi: boolean) => void;
  onSelectAll?: () => void;
  onActivate: (file: AudioFile) => void;
  sortConfig: SortConfig[];
  onSort: (config: SortConfig[]) => void;
  onContextMenu?: (e: React.MouseEvent, id: string) => void;

  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  itemsPerPage?: number;
  onItemsPerPageChange?: (items: number) => void;
}

interface ColumnDef {
  id: SortKey | "select" | "actions";
  label: string;
  defaultWidth: number;
}

const DEFAULT_COLUMNS: ColumnDef[] = [
  { id: "select", label: "#", defaultWidth: 80 },
  { id: "title", label: "Tytuł / Artysta", defaultWidth: 300 },
  { id: "bpm", label: "BPM", defaultWidth: 80 },
  { id: "key", label: "Tonacja", defaultWidth: 100 },
  { id: "genre", label: "Gatunek", defaultWidth: 150 },
  { id: "album", label: "Album", defaultWidth: 180 },
  { id: "year", label: "Rok", defaultWidth: 80 },
  { id: "rating", label: "Ocena", defaultWidth: 120 },
  { id: "energy", label: "Energa", defaultWidth: 100 },
  { id: "recordLabel", label: "Label", defaultWidth: 150 },
  { id: "mood", label: "Nastrój", defaultWidth: 120 },
  { id: "trackNumber", label: "Nr", defaultWidth: 60 },
  { id: "bitrate", label: "kbps", defaultWidth: 90 },
  { id: "albumArtist", label: "Artysta Albumu", defaultWidth: 180 },
  { id: "composer", label: "Kompozytor", defaultWidth: 180 },
  { id: "isrc", label: "ISRC", defaultWidth: 140 },
  { id: "danceability", label: "Taneczność", defaultWidth: 100 },
  { id: "sampleRate", label: "Sample Rate", defaultWidth: 110 },
  { id: "encodedBy", label: "Encoder", defaultWidth: 140 },
  { id: "originalArtist", label: "Oryg. Artysta", defaultWidth: 180 },
  { id: "copyright", label: "Copyright", defaultWidth: 200 },
  { id: "discNumber", label: "Dysk", defaultWidth: 60 },
  { id: "dateAdded", label: "Dodano", defaultWidth: 140 },
  { id: "actions", label: "", defaultWidth: 60 },
];

const TrackTable: React.FC<TrackTableProps> = ({
  files,
  selectedFileIds,
  activeFileId,
  onSelect,
  onActivate,
  onContextMenu,
  currentPage = 1,
  totalPages = 1,
  onPageChange,
  onSort,
  sortConfig,
}) => {
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>(() => {
    const saved = localStorage.getItem('trackTableColumnWidths');
    if (saved) return JSON.parse(saved);
    return Object.fromEntries(DEFAULT_COLUMNS.map(c => [c.id, c.defaultWidth]));
  });

  const resizingRef = useRef<{ id: string; startX: number; startWidth: number } | null>(null);

  const startResize = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    resizingRef.current = {
      id,
      startX: e.clientX,
      startWidth: columnWidths[id] || 100
    };

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!resizingRef.current) return;
      const delta = moveEvent.clientX - resizingRef.current.startX;
      const newWidth = Math.max(40, resizingRef.current.startWidth + delta);
      
      setColumnWidths(prev => {
        const updated = { ...prev, [resizingRef.current!.id]: newWidth };
        localStorage.setItem('trackTableColumnWidths', JSON.stringify(updated));
        return updated;
      });
    };

    const handleMouseUp = () => {
      resizingRef.current = null;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.classList.remove('cursor-col-resize');
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.classList.add('cursor-col-resize');
  }, [columnWidths]);

  const handleSort = (key: string) => {
    if (key === 'select' || key === 'actions') return;
    
    const existing = sortConfig.find(c => c.key === key);
    if (existing) {
      if (existing.direction === 'asc') {
        onSort([{ key: key as SortKey, direction: 'desc' }]);
      } else {
        onSort([]);
      }
    } else {
      onSort([{ key: key as SortKey, direction: 'asc' }]);
    }
  };

  const renderStars = (rating: number | undefined) => {
    const val = rating || 0;
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <svg 
            key={i} 
            xmlns="http://www.w3.org/2000/svg" 
            className={`h-3 w-3 ${i <= val ? "text-[var(--accent-cyan)] glow-cyan" : "text-white/10"}`} 
            viewBox="0 0 20 20" 
            fill="currentColor"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
    );
  };

  const renderCell = (file: AudioFile, colId: string) => {
    const tags = file.fetchedTags || file.originalTags || {};
    const isActive = activeFileId === file.id;

    switch (colId) {
      case "select":
        return null; // Handled separately
      case "title":
        return (
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-bold text-white group-hover:text-[var(--accent-cyan)] transition-colors truncate">{tags.title || file.file.name}</span>
            <span className="text-[10px] text-white/40 uppercase tracking-widest font-bold truncate">{tags.artist || "UNKNOWN"}</span>
          </div>
        );
      case "bpm":
        return <span className="text-xs font-mono text-white/60 font-bold">{tags.bpm || "---"}</span>;
      case "key":
        return (
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${isActive ? 'bg-[var(--accent-magenta)] text-white border-transparent' : 'bg-white/5 text-[var(--accent-magenta)] border-white/10 font-bold'}`}>
            {tags.initialKey || "---"}
          </span>
        );
      case "genre":
        return <span className="text-xs text-white/40 font-medium truncate block">{tags.genre || "---"}</span>;
      case "rating":
        return <div className="flex h-full items-center">{renderStars(tags.rating)}</div>;
      case "dateAdded":
        return new Date(file.dateAdded).toLocaleDateString('pl-PL', { month: 'short', day: 'numeric', year: 'numeric' });
      case "album":
        return <span className="text-xs text-white/60 truncate block">{tags.album || "---"}</span>;
      case "year":
        return <span className="text-xs text-white/40 font-mono italic">{tags.year || "---"}</span>;
      case "energy":
        return <span className={`text-[10px] font-bold ${tags.energy ? 'text-[var(--accent-cyan)]' : 'text-white/10'}`}>{tags.energy ? `${tags.energy}/10` : '---'}</span>;
      case "recordLabel":
        return <span className="text-xs text-white/50 truncate block uppercase tracking-tight">{tags.recordLabel || "---"}</span>;
      case "mood":
        return <span className="text-xs text-white/40 truncate block capitalize">{tags.mood || "---"}</span>;
      case "trackNumber":
        return <span className="text-xs font-mono text-white/30">{tags.trackNumber || "--"}</span>;
      case "bitrate":
        return <span className="text-[10px] font-mono text-white/20">{tags.bitrate ? `${tags.bitrate}k` : "---"}</span>;
      case "albumArtist":
        return <span className="text-xs text-white/40 truncate block">{tags.albumArtist || "---"}</span>;
      case "composer":
        return <span className="text-xs text-white/30 italic truncate block">{tags.composer || "---"}</span>;
      case "isrc":
        return <span className="text-[10px] font-mono text-white/20 uppercase">{tags.isrc || "---"}</span>;
      case "danceability":
        return <span className={`text-[10px] font-bold ${tags.danceability ? 'text-[var(--accent-magenta)]' : 'text-white/10'}`}>{tags.danceability ? `${tags.danceability}/10` : '---'}</span>;
      case "sampleRate":
        return <span className="text-[10px] font-mono text-white/20">{tags.sampleRate ? `${tags.sampleRate}Hz` : "---"}</span>;
      case "encodedBy":
        return <span className="text-xs text-white/30 truncate block">{tags.encodedBy || "---"}</span>;
      case "originalArtist":
        return <span className="text-xs text-white/40 truncate block">{tags.originalArtist || "---"}</span>;
      case "copyright":
        return <span className="text-[9px] text-white/20 truncate block">{tags.copyright || "---"}</span>;
      case "discNumber":
        return <span className="text-xs font-mono text-white/30">{tags.discNumber || "--"}</span>;
      case "actions":
        return (
          <button className="p-1 text-white/10 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/></svg>
          </button>
        );
      default:
        return null;
    }
  };

  if (files.length === 0) return (
    <div className="flex-grow flex items-center justify-center text-white/20">
      <p>Brak utworów spełniających kryteria</p>
    </div>
  );

  return (
    <div className="flex-grow flex flex-col h-full overflow-hidden bg-transparent select-none">
      <div className="flex-grow overflow-auto min-h-0 scrollbar-custom">
        <table className="min-w-full border-separate border-spacing-0 table-fixed">
          <thead className="sticky top-0 z-20">
            <tr className="bg-[var(--bg-base)]/80 backdrop-blur-md ">
              {DEFAULT_COLUMNS.map((col) => {
                const sort = sortConfig.find(c => c.key === col.id);
                const isSortable = col.id !== 'select' && col.id !== 'actions';
                
                return (
                  <th 
                    key={col.id}
                    style={{ width: columnWidths[col.id] || 100 }}
                    className={`relative px-4 py-3 text-[10px] uppercase tracking-[0.2em] font-bold text-white/30 border-b border-white/5 text-left group/header ${isSortable ? 'cursor-pointer hover:text-white' : ''}`}
                    onClick={() => handleSort(col.id)}
                  >
                    <div className="flex items-center gap-1 overflow-hidden">
                      <span className="truncate">{col.label}</span>
                      {sort && (
                         <span className="text-[var(--accent-cyan)] shrink-0">
                           {sort.direction === 'asc' ? '↑' : '↓'}
                         </span>
                      )}
                    </div>
                    {/* Resize handle */}
                    <div 
                      onMouseDown={(e) => startResize(col.id, e)}
                      onClick={(e) => e.stopPropagation()}
                      className="absolute top-0 right-0 bottom-0 w-1 cursor-col-resize hover:bg-[var(--accent-cyan)]/50 transition-colors opacity-0 group-hover/header:opacity-100 z-30"
                    />
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {files.map((file, idx) => {
              const isActive = activeFileId === file.id;
              const isSelected = selectedFileIds.includes(file.id);

              return (
                <tr
                  key={file.id}
                  onClick={(e) => {
                    const isMulti = e.ctrlKey || e.metaKey || e.shiftKey;
                    if (isMulti) {
                      onSelect(file.id, true);
                    } else {
                      onActivate(file);
                    }
                  }}
                  onDoubleClick={() => onActivate(file)}
                  onContextMenu={(e) => onContextMenu?.(e, file.id)}
                  className={`group transition-all cursor-pointer relative ${isActive ? 'bg-[var(--accent-cyan)]/10' : isSelected ? 'bg-white/5' : 'hover:bg-white/[0.03]'} ${isActive ? 'active-row' : ''}`}
                >
                  {DEFAULT_COLUMNS.map((col) => (
                    <td key={col.id} className={`px-4 py-3 overflow-hidden ${col.id === 'select' || col.id === 'actions' || col.id === 'bpm' || col.id === 'key' ? 'text-center' : ''} ${col.id === 'dateAdded' ? 'text-right' : ''}`}>
                      {col.id === "select" ? (
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              e.stopPropagation();
                              onSelect(file.id, true);
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="h-3 w-3 border border-white/20 bg-transparent rounded-sm checked:bg-[var(--accent-cyan)] focus:ring-0 cursor-pointer"
                          />
                          <div className="relative h-4 flex items-center justify-center min-w-[20px]">
                             <span className="group-hover:opacity-0 transition-opacity text-[10px] font-mono text-white/20">{(currentPage - 1) * files.length + idx + 1}</span>
                             <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 absolute text-[var(--accent-cyan)] opacity-0 group-hover:opacity-100 transition-opacity" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                             </svg>
                          </div>
                        </div>
                      ) : (
                        <div className={`overflow-hidden ${col.id === 'dateAdded' ? 'text-[10px] text-white/20 font-bold uppercase tracking-wider' : ''}`}>
                          {renderCell(file, col.id)}
                        </div>
                      )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 bg-white/[0.02] border-t border-white/5 p-4 shrink-0 transition-all">
           <button 
             onClick={() => onPageChange?.(Math.max(1, currentPage - 1))}
             disabled={currentPage === 1}
             className={`p-2 rounded-lg transition-all ${currentPage === 1 ? 'text-white/10 cursor-not-allowed' : 'text-white hover:bg-white/5 active:scale-90'}`}
           >
             <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
           </button>
           <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold tracking-widest text-[var(--accent-cyan)] font-mono">{currentPage}</span>
              <span className="text-[10px] font-bold tracking-widest text-white/20 uppercase">z {totalPages}</span>
           </div>
           <button 
             onClick={() => onPageChange?.(Math.min(totalPages, currentPage + 1))}
             disabled={currentPage === totalPages}
             className={`p-2 rounded-lg transition-all ${currentPage === totalPages ? 'text-white/10 cursor-not-allowed' : 'text-white hover:bg-white/5 active:scale-90'}`}
           >
             <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" /></svg>
           </button>
        </div>
      )}
    </div>
  );
};

export default TrackTable;
