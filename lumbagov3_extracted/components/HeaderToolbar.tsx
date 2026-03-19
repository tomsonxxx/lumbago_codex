
import React from 'react';

interface HeaderToolbarProps {
  totalCount: number;
  selectedCount: number;
  isAnalyzing: boolean;
  isSaving: boolean;
  allSelected: boolean;
  onToggleSelectAll: () => void;
  onAnalyze: () => void;
  onAnalyzeAll: () => void;
  onDownloadOrSave: () => void;
  onEdit: () => void;
  onRename: () => void;
  onExportCsv: () => void;
  onDelete: () => void;
  onClearAll: () => void;
  isDirectAccessMode: boolean;
  directoryName?: string;
  isRestored?: boolean;
  // Nowe propsy dla wyszukiwania i widoku
  searchQuery: string;
  onSearchChange: (query: string) => void;
  viewMode: 'list' | 'grid';
  onViewModeChange: (mode: 'list' | 'grid') => void;
  onToggleFilters: () => void;
  showFilters: boolean;
}

const ActionButton: React.FC<{
  onClick: () => void;
  disabled: boolean;
  isLoading?: boolean;
  loadingText?: string;
  title: string;
  children: React.ReactNode;
  isDanger?: boolean;
}> = ({ onClick, disabled, isLoading = false, loadingText = "Przetwarzam...", title, children, isDanger = false }) => {
  const baseClasses = "px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider rounded-lg flex items-center justify-center transition-all focus:outline-none";
  const colorClasses = isDanger
    ? "text-red-400 bg-red-900/20 hover:bg-red-900/40 border border-red-900/50"
    : "text-cyan-400 bg-cyan-900/20 hover:bg-cyan-900/40 border border-cyan-900/50 hover:shadow-[0_0_10px_rgba(34,211,238,0.2)]";
  const disabledClasses = "disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none";
  
  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      title={title}
      className={`${baseClasses} ${colorClasses} ${disabledClasses}`}
    >
      {isLoading ? (
          <>
            <span className="btn-spinner !mr-2 h-3 w-3"></span>
            <span>{loadingText}</span>
          </>
      ) : (
        children
      )}
    </button>
  );
};

const HeaderToolbar: React.FC<HeaderToolbarProps> = ({
  totalCount,
  selectedCount,
  isAnalyzing,
  isSaving,
  allSelected,
  onToggleSelectAll,
  onAnalyze,
  onAnalyzeAll,
  onDownloadOrSave,
  onEdit,
  onRename,
  onExportCsv,
  onDelete,
  onClearAll,
  isDirectAccessMode,
  directoryName,
  isRestored = false,
  searchQuery,
  onSearchChange,
  viewMode,
  onViewModeChange,
  onToggleFilters,
  showFilters
}) => {
  const hasSelection = selectedCount > 0;
  const isAnyLoading = isAnalyzing || isSaving;

  return (
    <div className="px-4 py-3 mb-2 flex flex-col gap-3">
        {/* Górny rząd: Search & Stats */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
                 <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Kolejka</h2>
                 <span className="bg-slate-800 text-cyan-400 text-xs font-bold px-2 py-0.5 rounded-full border border-slate-700">
                    {totalCount}
                 </span>
                 {isDirectAccessMode && (
                    <span className="text-xs text-slate-500 font-mono bg-slate-900 px-2 py-0.5 rounded border border-slate-800 truncate max-w-[200px]" title={directoryName}>
                        {directoryName}
                    </span>
                )}
            </div>

            <div className="flex items-center gap-3 flex-grow md:justify-end">
                {/* Wyszukiwarka */}
                <div className="relative flex-grow md:max-w-xs group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg className="h-4 w-4 text-slate-600 group-focus-within:text-cyan-500 transition-colors" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <input
                        type="text"
                        placeholder="Szukaj..."
                        value={searchQuery}
                        onChange={(e) => onSearchChange(e.target.value)}
                        className="block w-full pl-9 pr-3 py-1.5 border border-slate-800 rounded-full leading-5 bg-slate-900 text-slate-300 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:bg-slate-800 sm:text-sm transition-all"
                    />
                </div>
                
                <button
                    onClick={onToggleFilters}
                    className={`p-1.5 rounded-lg border transition-all ${showFilters ? 'bg-indigo-900/50 border-indigo-500/50 text-indigo-300' : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-white'}`}
                    title="Filtry"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                    </svg>
                </button>
            </div>
        </div>

        {/* Dolny rząd: Akcje masowe */}
        <div className="flex flex-wrap items-center gap-2">
             <button
                onClick={onToggleSelectAll}
                disabled={isAnyLoading}
                className="mr-2 text-xs font-bold text-slate-500 hover:text-white transition-colors disabled:opacity-50"
            >
                {allSelected ? 'Odznacz wszystko' : 'Zaznacz wszystko'}
            </button>
            
            <div className="h-4 w-px bg-slate-800 mx-1 hidden sm:block"></div>

            <ActionButton
                onClick={onAnalyze}
                disabled={!hasSelection || isAnyLoading || isRestored}
                isLoading={isAnalyzing}
                loadingText="AI..."
                title="Analizuj zaznaczone pliki"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                ANALIZUJ
            </ActionButton>
             <ActionButton
                onClick={onDownloadOrSave}
                disabled={!hasSelection || isAnyLoading || isRestored}
                isLoading={isSaving}
                loadingText="..."
                title="Pobierz / Zapisz"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                {isDirectAccessMode ? "ZAPISZ" : "POBIERZ"}
            </ActionButton>
            
            <div className="flex-grow"></div>
            
            <ActionButton
                onClick={onEdit}
                disabled={!hasSelection || isAnyLoading}
                title="Edycja masowa"
            >
                EDYTUJ
            </ActionButton>
            <ActionButton
                onClick={onRename}
                disabled={isAnyLoading}
                title="Zmiana nazw"
            >
                NAZWY
            </ActionButton>
             <ActionButton
                onClick={onDelete}
                disabled={!hasSelection || isAnyLoading}
                title="Usuń zaznaczone"
                isDanger
            >
                USUŃ
            </ActionButton>
        </div>
    </div>
  );
};

export default HeaderToolbar;
