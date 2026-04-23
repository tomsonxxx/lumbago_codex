
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
  const baseClasses = "px-3 py-2 text-xs font-semibold rounded-md flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-900";
  const colorClasses = isDanger
    ? "text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/50 hover:bg-red-200 dark:hover:bg-red-900/80 disabled:bg-red-100/50 dark:disabled:bg-red-900/30 focus:ring-red-500"
    : "text-indigo-600 dark:text-indigo-300 bg-indigo-100 dark:bg-indigo-900/50 hover:bg-indigo-200 dark:hover:bg-indigo-900/80 disabled:bg-indigo-100/50 dark:disabled:bg-indigo-900/30 focus:ring-indigo-500";
  const disabledClasses = "disabled:cursor-not-allowed disabled:text-slate-400 dark:disabled:text-slate-600";
  
  return (
    <button
      onClick={onClick}
      disabled={disabled || isLoading}
      title={title}
      className={`${baseClasses} ${colorClasses} ${disabledClasses}`}
    >
      {isLoading ? (
          <>
            <span className="btn-spinner !mr-2 h-4 w-4"></span>
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
    <div className="p-4 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm sticky top-0 z-20">
        {/* Górny rząd: Tytuł, Search, Widok */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
            <div className="flex flex-col">
                 <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Biblioteka</h2>
                    <span className="bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-bold px-2 py-0.5 rounded-full">
                        {totalCount}
                    </span>
                 </div>
                 {isDirectAccessMode && (
                    <div className="flex items-center text-xs text-slate-500 dark:text-slate-400 mt-1" title={`Pracujesz w folderze: ${directoryName}`}>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm2 2v1h12V8H4z" clipRule="evenodd" /></svg>
                        <span className="truncate max-w-[200px]">{directoryName}</span>
                    </div>
                )}
            </div>

            <div className="flex items-center gap-2 flex-grow md:justify-end">
                {/* Wyszukiwarka */}
                <div className="relative flex-grow md:max-w-xs group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <svg className="h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <input
                        type="text"
                        placeholder="Szukaj..."
                        value={searchQuery}
                        onChange={(e) => onSearchChange(e.target.value)}
                        className="block w-full pl-10 pr-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg leading-5 bg-white dark:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-shadow"
                    />
                </div>
                
                <div className="h-8 w-px bg-slate-300 dark:bg-slate-600 mx-1"></div>

                {/* Przełączniki Widoku */}
                 <div className="flex bg-slate-100 dark:bg-slate-700/50 p-1 rounded-lg border border-slate-200 dark:border-slate-600">
                    <button
                        onClick={() => onViewModeChange('list')}
                        className={`p-1.5 rounded-md transition-all ${viewMode === 'list' ? 'bg-white dark:bg-slate-600 text-indigo-600 dark:text-indigo-300 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                        title="Widok listy"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                    </button>
                    <button
                        onClick={() => onViewModeChange('grid')}
                        className={`p-1.5 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white dark:bg-slate-600 text-indigo-600 dark:text-indigo-300 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'}`}
                        title="Widok siatki"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
                    </button>
                </div>

                <button
                    onClick={onToggleFilters}
                    className={`p-2 rounded-lg border transition-colors ${showFilters ? 'bg-indigo-100 dark:bg-indigo-900/50 border-indigo-200 dark:border-indigo-800 text-indigo-600 dark:text-indigo-300' : 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                    title="Pokaż/Ukryj filtry"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                    </svg>
                </button>
            </div>
        </div>

        {/* Dolny rząd: Akcje masowe */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-200 dark:border-slate-700">
             <button
                onClick={onToggleSelectAll}
                disabled={isAnyLoading}
                className="mr-2 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors disabled:opacity-50"
            >
                {allSelected ? 'Odznacz wszystko' : 'Zaznacz wszystko'}
            </button>
            
            <div className="h-6 w-px bg-slate-300 dark:bg-slate-600 mx-1 hidden sm:block"></div>

            <ActionButton
                onClick={onAnalyzeAll}
                disabled={totalCount === 0 || isAnyLoading || isRestored}
                isLoading={isAnalyzing}
                loadingText="Analizuję..."
                title={isRestored ? "Załaduj pliki ponownie, aby je analizować" : "Analizuj wszystkie nieprzetworzone pliki"}
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 4a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2V6a2 2 0 00-2-2H5zM5 16a2 2 0 00-2 2v.5a.5.5 0 00.5.5h13a.5.5 0 00.5-.5V18a2 2 0 00-2-2H5z" /></svg>
                Analizuj wszystko
            </ActionButton>
            <ActionButton
                onClick={onAnalyze}
                disabled={!hasSelection || isAnyLoading || isRestored}
                isLoading={isAnalyzing}
                loadingText="Analizuję..."
                title={isRestored ? "Załaduj pliki ponownie, aby je analizować" : "Analizuj zaznaczone pliki"}
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                Analizuj zaznaczone
            </ActionButton>
             <ActionButton
                onClick={onDownloadOrSave}
                disabled={!hasSelection || isAnyLoading || isRestored}
                isLoading={isSaving}
                loadingText={isDirectAccessMode ? "Zapisuję..." : "Pobieram..."}
                title={isRestored ? "Załaduj pliki ponownie, aby je zapisać" : isDirectAccessMode ? "Zapisz zmiany w plikach" : "Pobierz zaznaczone pliki jako ZIP"}
            >
                {isDirectAccessMode ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" /></svg>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                )}
                {isDirectAccessMode ? "Zapisz zmiany" : "Pobierz"}
            </ActionButton>
            
            <div className="flex-grow"></div>
            
            <ActionButton
                onClick={onEdit}
                disabled={!hasSelection || isAnyLoading}
                title="Edytuj masowo zaznaczone pliki"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" /><path fillRule="evenodd" d="M2 6a2 2 0 012-2h4a1 1 0 010 2H4v10h10v-4a1 1 0 112 0v4a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" /></svg>
                Edytuj
            </ActionButton>
            <ActionButton
                onClick={onRename}
                disabled={isAnyLoading}
                title="Ustaw szablon zmiany nazw dla wszystkich plików"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
                Zmień nazwy
            </ActionButton>
             <ActionButton
                onClick={onDelete}
                disabled={!hasSelection || isAnyLoading}
                title="Usuń zaznaczone pliki"
                isDanger
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                Usuń
            </ActionButton>
            <div className="border-l border-slate-300 dark:border-slate-600 h-6 mx-2"></div>
            <button 
                onClick={onClearAll}
                disabled={isAnyLoading}
                title="Wyczyść całą kolejkę"
                className="px-3 py-2 text-xs font-semibold text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/50 rounded-md hover:bg-red-200 dark:hover:bg-red-900/80 transition-colors disabled:opacity-50"
            >
                {isDirectAccessMode ? "Zamknij folder" : "Wyczyść wszystko"}
            </button>
        </div>
    </div>
  );
};

export default HeaderToolbar;
