
import React, { useState, useMemo } from 'react';
import { AudioFile, ProcessingState } from '../types';
import HeaderToolbar from './HeaderToolbar';
import FileListItem from './FileListItem';
import FileGridItem from './FileGridItem';
import FilterSidebar from './FilterSidebar';

interface LibraryTabProps {
  files: AudioFile[];
  sortedFiles: AudioFile[]; // To są pliki posortowane, ale jeszcze nie przefiltrowane przez Search/Sidebar
  selectedFiles: AudioFile[];
  allFilesSelected: boolean;
  isBatchAnalyzing: boolean;
  isSaving: boolean;
  directoryHandle: any | null;
  isRestored: boolean;
  onToggleSelectAll: () => void;
  onBatchAnalyze: (files: AudioFile[]) => void;
  onBatchAnalyzeAll: () => void;
  onDownloadOrSave: () => void;
  onBatchEdit: () => void;
  onSingleItemEdit: (fileId: string) => void;
  onRename: () => void;
  onExportCsv: () => void;
  onDeleteItem: (id: string | 'selected' | 'all') => void;
  onClearAll: () => void;
  onProcessFile: (file: AudioFile) => void;
  onSelectionChange: (fileId: string, isSelected: boolean) => void;
  onTabChange: (tabId: string) => void;
}

const LibraryTab: React.FC<LibraryTabProps> = (props) => {
  // --- Stan Lokalny dla UI Biblioteki ---
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [activeFilters, setActiveFilters] = useState<{
      genre: string | null;
      year: string | null;
      status: ProcessingState | null | 'PROCESSED';
  }>({
      genre: null,
      year: null,
      status: null
  });

  // --- Logika Filtrowania ---
  // Używamy props.files (wszystkie) do budowy filtrów, ale props.sortedFiles do wyświetlania kolejności
  // Najpierw sortujemy (robi to App.tsx), potem filtrujemy tutaj.
  
  const filteredFiles = useMemo(() => {
    let result = props.sortedFiles;

    // 1. Wyszukiwarka tekstowa
    if (searchQuery.trim()) {
        const lowerQuery = searchQuery.toLowerCase();
        result = result.filter(file => {
            const tags = file.fetchedTags || file.originalTags;
            return (
                file.file.name.toLowerCase().includes(lowerQuery) ||
                (tags?.title && tags.title.toLowerCase().includes(lowerQuery)) ||
                (tags?.artist && tags.artist.toLowerCase().includes(lowerQuery)) ||
                (tags?.album && tags.album.toLowerCase().includes(lowerQuery))
            );
        });
    }

    // 2. Filtry Boczne
    if (activeFilters.genre) {
        result = result.filter(f => {
             const g = f.fetchedTags?.genre || f.originalTags?.genre;
             return g === activeFilters.genre;
        });
    }

    if (activeFilters.year) {
        result = result.filter(f => {
             const y = f.fetchedTags?.year || f.originalTags?.year;
             return y === activeFilters.year;
        });
    }

    if (activeFilters.status) {
        if (activeFilters.status === ProcessingState.SUCCESS) {
             result = result.filter(f => f.state === ProcessingState.SUCCESS);
        } else if (activeFilters.status === ProcessingState.ERROR) {
             result = result.filter(f => f.state === ProcessingState.ERROR);
        } else if (activeFilters.status === ProcessingState.PENDING) {
             result = result.filter(f => f.state === ProcessingState.PENDING);
        }
    }

    return result;
  }, [props.sortedFiles, searchQuery, activeFilters]);


  const handleFilterChange = (key: 'genre' | 'year' | 'status', value: any) => {
      setActiveFilters(prev => ({ ...prev, [key]: value }));
  };

  if (props.files.length === 0) {
    return (
      <div className="text-center p-10 bg-slate-100 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 animate-fade-in">
        <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-200">Twoja biblioteka jest pusta</h2>
        <p className="text-slate-500 dark:text-slate-400 mt-2 mb-4">
          Przejdź do zakładki "Import / Skan", aby dodać pliki audio.
        </p>
        <button
          onClick={() => props.onTabChange('scan')}
          className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500 transition-colors"
        >
          Przejdź do Importu
        </button>
      </div>
    );
  }

  return (
    <div className="relative min-h-[500px]"> {/* Min-height dla stabilności layoutu przy pustym filtrze */}
       {props.isRestored && (
            <div className="my-4 p-3 bg-yellow-100 dark:bg-yellow-900/50 border-l-4 border-yellow-500 text-yellow-800 dark:text-yellow-300 rounded-r-lg animate-fade-in" role="alert">
                <div className="flex justify-between items-center gap-4">
                    <div>
                        <p className="font-bold">Sesja przywrócona</p>
                        <p className="text-sm">Twoja poprzednia lista plików została wczytana. Aby zapisać lub pobrać pliki, musisz je ponownie załadować w zakładce "Import / Skan".</p>
                    </div>
                    <button
                        onClick={props.onClearAll}
                        className="px-3 py-1.5 text-xs font-semibold text-yellow-800 dark:text-yellow-200 bg-yellow-200 dark:bg-yellow-800/60 rounded-md hover:bg-yellow-300 dark:hover:bg-yellow-800/90 transition-colors flex-shrink-0"
                    >
                        Wyczyść listę
                    </button>
                </div>
            </div>
        )}

      <HeaderToolbar
        totalCount={props.files.length}
        selectedCount={props.selectedFiles.length}
        isAnalyzing={props.isBatchAnalyzing}
        isSaving={props.isSaving}
        allSelected={props.allFilesSelected}
        onToggleSelectAll={props.onToggleSelectAll}
        onAnalyze={() => props.onBatchAnalyze(props.selectedFiles)}
        onAnalyzeAll={props.onBatchAnalyzeAll}
        onDownloadOrSave={props.onDownloadOrSave}
        onEdit={props.onBatchEdit}
        onRename={props.onRename}
        onExportCsv={props.onExportCsv}
        onDelete={() => props.onDeleteItem('selected')}
        onClearAll={props.onClearAll}
        isDirectAccessMode={!!props.directoryHandle}
        directoryName={props.directoryHandle?.name}
        isRestored={props.isRestored}
        // New props
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        onToggleFilters={() => setShowFilters(!showFilters)}
        showFilters={showFilters}
      />
      
      {/* Sidebar Filtrów */}
      <FilterSidebar 
          files={props.files}
          filters={activeFilters}
          onFilterChange={handleFilterChange}
          isOpen={showFilters}
          onClose={() => setShowFilters(false)}
      />

      {/* Kontener listy plików */}
      <div className="mt-4 pb-20">
        {filteredFiles.length === 0 ? (
            <div className="text-center py-20 opacity-60">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4 text-slate-300 dark:text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                <p className="text-lg text-slate-500 dark:text-slate-400">Nie znaleziono plików pasujących do kryteriów.</p>
                <button onClick={() => { setSearchQuery(''); setActiveFilters({ genre: null, year: null, status: null }); }} className="mt-2 text-indigo-500 hover:underline">Wyczyść filtry</button>
            </div>
        ) : viewMode === 'list' ? (
            <div className="space-y-3">
              {/* Table Header */}
              <div className="hidden md:flex items-center px-3 py-2 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700 mb-2">
                <div className="w-5 mr-4"></div> {/* Checkbox space */}
                <div className="w-6 mr-2"></div> {/* Status space */}
                <div className="w-10"></div> {/* Cover space */}
                <div className="flex-grow ml-4">Utwór / Nazwa pliku</div>
                <div className="w-20 ml-4 text-center">BPM</div>
                <div className="w-20 ml-4 text-center">Klucz</div>
                <div className="w-28 ml-4 text-right">Akcje</div>
              </div>
              {filteredFiles.map(file => (
                <FileListItem 
                  key={file.id} 
                  file={file} 
                  onProcess={props.onProcessFile}
                  onEdit={(f) => props.onSingleItemEdit(f.id)}
                  onDelete={props.onDeleteItem}
                  onSelectionChange={props.onSelectionChange}
                />
              ))}
            </div>
        ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                 {filteredFiles.map(file => (
                    <FileGridItem
                        key={file.id}
                        file={file}
                        onProcess={props.onProcessFile}
                        onEdit={(f) => props.onSingleItemEdit(f.id)}
                        onSelectionChange={props.onSelectionChange}
                    />
                 ))}
            </div>
        )}
      </div>
    </div>
  );
};

export default LibraryTab;
