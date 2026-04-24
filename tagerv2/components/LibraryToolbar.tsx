import React from "react";

interface LibraryToolbarProps {
  onImport: () => void;
  onSettings: () => void;
  onAnalyzeAll: () => void;
  onAnalyzeSelected: () => void;
  onForceAnalyzeSelected: () => void;
  onEdit: () => void;
  onExport: () => void;
  onDelete: () => void;
  onClearAll: () => void;
  onRename: () => void;
  onFindDuplicates: () => void;
  onExportCsv: () => void;
  onConvertXml: () => void; // New

  selectedCount: number;
  totalCount: number;
  allSelected: boolean;
  onToggleSelectAll: () => void;

  theme: "light" | "dark";
  setTheme: (theme: "light" | "dark") => void;
  isProcessing: boolean;

  isDirectAccessMode: boolean;
  directoryName?: string;
  isRestored?: boolean;

  // Search & View Props
  searchQuery: string;
  onSearchChange: (query: string) => void;
  viewMode: "list" | "grid";
  onViewModeChange: (mode: "list" | "grid") => void;
  showFilters: boolean;
  onToggleFilters: () => void;
}

const LibraryToolbar: React.FC<LibraryToolbarProps> = ({
  searchQuery,
  onSearchChange,
  onToggleFilters,
  showFilters,
  onImport,
  onSettings,
  onAnalyzeAll,
  onAnalyzeSelected,
  onEdit,
  onExport,
  onDelete,
  onClearAll,
  onRename,
  onFindDuplicates,
  onConvertXml,
  selectedCount,
  totalCount,
  isProcessing,
  isDirectAccessMode,
  directoryName,
}) => {
  return (
    <header className="h-24 glass-effect border-b border-white/5 flex flex-col flex-shrink-0 z-20 relative">
      <div className="flex-1 flex items-center justify-between px-8">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-gradient-to-br from-[var(--accent-magenta)] to-[var(--accent-blue)] rounded-xl shadow-lg glow-magenta">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15V6a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v9"/>
              <path d="m21 9-9-4-9 4"/>
              <path d="M3 15h18V21a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6Z"/>
            </svg>
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-bold tracking-tight text-white font-heading leading-tight">
              Biblioteka
            </h1>
            <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest leading-none">
              {totalCount} Utworów {isDirectAccessMode ? `• ${directoryName}` : ""}
            </p>
          </div>
        </div>

        <div className="flex-1 max-w-xl mx-8">
          <div className="relative group">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-full py-2.5 px-10 focus:outline-none focus:ring-2 focus:ring-[var(--accent-cyan)]/50 focus:bg-white/10 transition-all font-medium text-sm text-white placeholder:text-white/20"
              placeholder="Szukaj..."
            />
            <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none text-white/30">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            {searchQuery && (
               <button 
                onClick={() => onSearchChange("")}
                className="absolute inset-y-0 right-3.5 flex items-center text-white/20 hover:text-white transition-colors"
               >
                 <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                   <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586l-1.293-1.293z" clipRule="evenodd" />
                 </svg>
               </button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onToggleFilters}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${showFilters ? "bg-[var(--accent-cyan)] text-black glow-cyan" : "bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/10"}`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            FILTRY
          </button>
          
          <div className="h-6 w-px bg-white/10 mx-1" />

          <button
            onClick={onSettings}
            className="p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-all"
            title="Ustawienia"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Secondary Bar for Actions */}
      <div className="h-10 bg-black/20 flex items-center px-8 gap-6 border-t border-white/5">
        <div className="flex items-center gap-4">
          <button 
            onClick={onImport}
            className="text-[10px] uppercase font-bold text-white/40 hover:text-white transition-colors flex items-center gap-1.5"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" /></svg>
            DODAJ PLIKI
          </button>
          <button 
             onClick={onAnalyzeAll}
             disabled={isProcessing}
             className="text-[10px] uppercase font-bold text-[var(--accent-magenta)] hover:text-white transition-colors flex items-center gap-1.5 group disabled:opacity-30"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 animate-pulse group-hover:animate-none" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
            AUTO-TAG ALL
          </button>
        </div>

        <div className="h-4 w-px bg-white/10" />

        <div className="flex items-center gap-4 flex-1">
          {selectedCount > 0 ? (
            <>
              <span className="text-[10px] font-bold text-[var(--accent-cyan)] glow-cyan uppercase">
                Zaznaczono {selectedCount}
              </span>
              <button onClick={onAnalyzeSelected} className="tech-action-btn">AI ANALIZA</button>
              <button onClick={onEdit} className="tech-action-btn">EDYCJA</button>
              <button onClick={onRename} className="tech-action-btn">ZMIEŃ NAZWĘ</button>
              <button onClick={onExport} className="tech-action-btn text-[var(--accent-magenta)]">EKSPORTUJ</button>
              <button onClick={onDelete} className="tech-action-btn text-red-500/70 hover:text-red-400">USUŃ</button>
            </>
          ) : (
            <div className="flex items-center gap-4 opacity-40 grayscale pointer-events-none">
              <span className="text-[10px] text-white/50 uppercase font-bold">Wybierz utwory, aby wykonać akcje</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
           <button onClick={onFindDuplicates} className="text-[10px] font-bold text-white/30 hover:text-white transition-colors uppercase">Szukaj Duplikatów</button>
           <button onClick={onConvertXml} className="text-[10px] font-bold text-white/30 hover:text-white transition-colors uppercase">XML Konwerter</button>
           <button onClick={onClearAll} className="text-[10px] font-bold text-red-500/30 hover:text-red-500 transition-colors uppercase">Wyczyść</button>
        </div>
      </div>

      <style>{`
        .tech-action-btn {
          @apply text-[10px] font-bold text-white/40 hover:text-white hover:bg-white/5 px-2 py-1 rounded transition-all uppercase tracking-wider;
        }
      `}</style>
    </header>
  );
};

export default LibraryToolbar;
