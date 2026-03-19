
import React from 'react';
import ThemeToggle from './ThemeToggle';

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
  
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  isProcessing: boolean;
  
  isDirectAccessMode: boolean;
  directoryName?: string;
  isRestored?: boolean;

  // Search & View Props
  searchQuery: string;
  onSearchChange: (query: string) => void;
  viewMode: 'list' | 'grid';
  onViewModeChange: (mode: 'list' | 'grid') => void;
  showFilters: boolean;
  onToggleFilters: () => void;
}

const LibraryToolbar: React.FC<LibraryToolbarProps> = ({
  onImport,
  onSettings,
  onAnalyzeAll,
  onAnalyzeSelected,
  onForceAnalyzeSelected,
  onEdit,
  onExport,
  onDelete,
  onClearAll,
  onRename,
  onFindDuplicates,
  onExportCsv,
  onConvertXml,
  
  selectedCount,
  totalCount,
  allSelected,
  onToggleSelectAll,
  
  theme,
  setTheme,
  isProcessing,
  
  isDirectAccessMode,
  directoryName,
  isRestored,

  searchQuery,
  onSearchChange,
  viewMode,
  onViewModeChange,
  showFilters,
  onToggleFilters
}) => {
  const hasSelection = selectedCount > 0;

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 flex-shrink-0 z-20 relative">
      
      {/* Left: Search & Import */}
      <div className="flex items-center space-x-3 md:space-x-4 flex-1">
        <div className="flex space-x-1">
            <button 
                onClick={onImport}
                disabled={isProcessing}
                className="flex items-center px-3 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-400 text-white text-sm font-bold rounded-l-md shadow-sm transition-colors"
                title="Importuj pliki lub foldery"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" /></svg>
                <span className="hidden lg:inline">Import</span>
            </button>
            <button 
                onClick={onImport} // Reuses import logic but labelled as Scan per plan
                disabled={isProcessing}
                className="flex items-center px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-600 text-white text-sm font-medium rounded-r-md shadow-sm transition-colors border-l border-slate-600"
                title="Skanuj folder"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" /></svg>
                <span className="hidden lg:inline ml-1">Skanuj</span>
            </button>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-md w-full">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-slate-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
            </div>
            <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-slate-300 dark:border-slate-700 rounded-md leading-5 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 sm:text-sm"
                placeholder="Szukaj..."
            />
        </div>

        <button 
            onClick={onToggleFilters}
            className={`p-2 rounded-md transition-colors ${showFilters ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400' : 'text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
            title="Filtry zaawansowane"
        >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clipRule="evenodd" /></svg>
        </button>
      </div>

      {/* Center: Actions */}
      <div className="flex items-center space-x-2 justify-center mx-4">
         {hasSelection ? (
            <div className="flex items-center space-x-1 bg-indigo-50 dark:bg-indigo-900/20 px-2 py-1 rounded-md animate-fade-in border border-indigo-100 dark:border-indigo-900/30">
                <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-300 mr-2 whitespace-nowrap">{selectedCount}</span>
                
                <button onClick={onAnalyzeSelected} disabled={isProcessing} className="p-1.5 hover:bg-indigo-200 dark:hover:bg-indigo-800 rounded text-indigo-600 dark:text-indigo-300 transition-colors" title="Tag AI (Cache)">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                </button>
                 <button onClick={onForceAnalyzeSelected} disabled={isProcessing} className="flex items-center px-2 py-1 ml-1 text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 rounded transition-colors" title="Tag AI (Web Update)">
                    Aktualizuj (Web)
                </button>
                <div className="w-px h-4 bg-indigo-200 dark:bg-indigo-800 mx-1"></div>
                <button onClick={onExport} disabled={isProcessing || isRestored} className="p-1.5 hover:bg-indigo-200 dark:hover:bg-indigo-800 rounded text-indigo-600 dark:text-indigo-300 transition-colors" title="Pobierz/Zapisz">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                </button>
                <button onClick={onDelete} disabled={isProcessing} className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/50 rounded text-red-600 dark:text-red-400 transition-colors" title="Usuń">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                </button>
            </div>
         ) : (
            <div className="flex items-center space-x-2 text-slate-600 dark:text-slate-300">
                 {/* Analyze All */}
                 <button onClick={onAnalyzeAll} disabled={isProcessing} className="flex items-center px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors" title="Analizuj wszystko (wypełnij braki)">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 md:mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M5 4a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2V6a2 2 0 00-2-2H5zM5 16a2 2 0 00-2 2v.5a.5.5 0 00.5.5h13a.5.5 0 00.5-.5V18a2 2 0 00-2-2H5z" /></svg>
                    <span className="hidden xl:inline text-sm font-medium">Tag AI</span>
                </button>
                
                <div className="w-px h-4 bg-slate-300 dark:bg-slate-700 mx-1"></div>

                 {/* Duplicates */}
                 <button onClick={onFindDuplicates} disabled={isProcessing || totalCount < 2} className="flex items-center px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors" title="Znajdź duplikaty">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 md:mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" /></svg>
                    <span className="hidden lg:inline text-sm font-medium">Duplikaty</span>
                </button>

                {/* Rename */}
                <button onClick={onRename} disabled={isProcessing} className="flex items-center px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors" title="Zmień Nazwy">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 md:mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
                    <span className="hidden lg:inline text-sm font-medium">Nazwy</span>
                </button>

                {/* CSV */}
                 <button onClick={onExportCsv} disabled={isProcessing} className="flex items-center px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors" title="Eksportuj CSV">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 md:mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" /></svg>
                    <span className="hidden lg:inline text-sm font-medium">CSV</span>
                </button>

                {/* XML Converter */}
                <button onClick={onConvertXml} disabled={isProcessing} className="flex items-center px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors" title="Konwertuj XML">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 md:mr-1.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                    <span className="hidden lg:inline text-sm font-medium">XML</span>
                </button>

                <div className="w-px h-4 bg-slate-300 dark:bg-slate-700 mx-1"></div>

                 <button onClick={onClearAll} disabled={isProcessing} className="p-2 hover:bg-red-100 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400 rounded transition-colors" title="Wyczyść wszystko">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                </button>
            </div>
         )}
      </div>

      {/* Right: View Toggle, Settings & Theme */}
      <div className="flex items-center space-x-2 md:space-x-3">
        {/* View Toggle */}
        <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg p-1 mr-2">
            <button 
                onClick={() => onViewModeChange('list')}
                className={`p-1.5 rounded-md transition-all ${viewMode === 'list' ? 'bg-white dark:bg-slate-600 shadow text-indigo-600 dark:text-white' : 'text-slate-400 hover:text-slate-600'}`}
                title="Widok listy"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
            <button 
                onClick={() => onViewModeChange('grid')}
                className={`p-1.5 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white dark:bg-slate-600 shadow text-indigo-600 dark:text-white' : 'text-slate-400 hover:text-slate-600'}`}
                title="Widok siatki"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
            </button>
        </div>

        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>
    </header>
  );
};

export default LibraryToolbar;
