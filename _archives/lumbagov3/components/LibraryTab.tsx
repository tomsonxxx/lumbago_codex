
import React, { useState, useMemo, useEffect } from 'react';
import { AudioFile, ProcessingState, ID3Tags } from '../types';
import HeaderToolbar from './HeaderToolbar';
import FileListItem from './FileListItem';
import FileGridItem from './FileGridItem';
import FilterSidebar from './FilterSidebar';
import AlbumCover from './AlbumCover';
import { SortKey } from '../utils/sortingUtils';

interface LibraryTabProps {
  files: AudioFile[];
  sortedFiles: AudioFile[]; 
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
  // Player props
  playingFileId: string | null;
  isPlaying: boolean;
  onPlayPause: (fileId: string) => void;
  // Inspector prop
  onInspectItem: (fileId: string) => void;
  // Playlist & Favs
  onToggleFavorite: (fileId: string) => void;
  onAddToPlaylist: (fileId: string) => void;
  // Sorting (Passed from App)
  currentSortKey?: SortKey;
  currentSortDirection?: 'asc' | 'desc';
  onSortChange?: (key: SortKey) => void;
}

const SortableHeader: React.FC<{ 
    label: string; 
    sortKey: SortKey; 
    currentKey?: SortKey; 
    direction?: 'asc' | 'desc'; 
    onClick?: (key: SortKey) => void;
    className?: string; 
}> = ({ label, sortKey, currentKey, direction, onClick, className }) => {
    const isActive = currentKey === sortKey;
    return (
        <div 
            className={`flex items-center cursor-pointer hover:text-cyan-400 transition-colors py-2 px-1 font-bold text-[10px] text-slate-500 uppercase tracking-wider ${className}`}
            onClick={() => onClick && onClick(sortKey)}
        >
            {label}
            <div className="ml-1 w-3 flex flex-col items-center">
                {isActive && (
                    direction === 'asc' 
                    ? <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" /></svg>
                    : <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                )}
            </div>
        </div>
    );
};

const LibraryTab: React.FC<LibraryTabProps> = (props) => {
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

  // Track currently shown in the right panel (Active Track)
  const [activeTrackId, setActiveTrackId] = useState<string | null>(null);

  // Sync active track with playing track if available, otherwise first selected, otherwise first in list
  useEffect(() => {
      if (props.playingFileId) {
          setActiveTrackId(props.playingFileId);
      } else if (props.selectedFiles.length > 0) {
          setActiveTrackId(props.selectedFiles[0].id);
      }
  }, [props.playingFileId, props.selectedFiles]);

  const activeTrack = useMemo(() => {
      return props.files.find(f => f.id === activeTrackId) || props.files.find(f => f.id === props.playingFileId) || (props.sortedFiles.length > 0 ? props.sortedFiles[0] : null);
  }, [activeTrackId, props.files, props.playingFileId, props.sortedFiles]);


  const filteredFiles = useMemo(() => {
    let result = props.sortedFiles;

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

  const handleSort = (key: SortKey) => {
      if (props.onSortChange) props.onSortChange(key);
  };

  if (props.files.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-10 bg-transparent animate-fade-in">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400 mb-4">Biblioteka jest pusta</h2>
        <p className="text-slate-500 mb-8 max-w-md">
          Przeciągnij i upuść pliki lub użyj kreatora importu, aby rozpocząć organizację swojej muzyki.
        </p>
        <button
          onClick={() => props.onTabChange('scan')}
          className="px-8 py-3 text-sm font-bold text-white bg-indigo-600 rounded-full hover:bg-indigo-500 hover:shadow-[0_0_20px_rgba(79,70,229,0.5)] transition-all transform hover:scale-105"
        >
          Przejdź do Importu
        </button>
      </div>
    );
  }

  // Grid layout for list view columns
  const gridTemplate = "md:grid-cols-[40px_minmax(200px,2fr)_minmax(150px,1.5fr)_minmax(150px,1.5fr)_60px_50px]";

  const activeTags = activeTrack?.fetchedTags || activeTrack?.originalTags;

  return (
    <div className="flex h-full bg-transparent overflow-hidden">
        
        {/* --- MAIN LIST AREA (Left/Center) --- */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-white/5">
            
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
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                onToggleFilters={() => setShowFilters(!showFilters)}
                showFilters={showFilters}
            />
            
            <FilterSidebar 
                files={props.files}
                filters={activeFilters}
                onFilterChange={handleFilterChange}
                isOpen={showFilters}
                onClose={() => setShowFilters(false)}
            />

            <div className="flex-1 overflow-y-auto px-4 pb-32 custom-scrollbar">
                {/* Table Header */}
                <div className={`hidden md:grid ${gridTemplate} gap-4 px-2 py-3 border-b border-white/5 sticky top-0 bg-[#050505]/95 z-10 backdrop-blur-sm mb-2`}>
                    <div className="flex items-center justify-center"><input type="checkbox" checked={props.allFilesSelected} onChange={props.onToggleSelectAll} className="h-4 w-4 rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer" /></div>
                    <SortableHeader label="OKŁADKA / TYTUŁ" sortKey="title" currentKey={props.currentSortKey} direction={props.currentSortDirection} onClick={handleSort} />
                    <SortableHeader label="ARTYSTA" sortKey="artist" currentKey={props.currentSortKey} direction={props.currentSortDirection} onClick={handleSort} />
                    <SortableHeader label="ALBUM" sortKey="album" currentKey={props.currentSortKey} direction={props.currentSortDirection} onClick={handleSort} />
                    <SortableHeader label="BPM" sortKey="bpm" currentKey={props.currentSortKey} direction={props.currentSortDirection} onClick={handleSort} />
                    <SortableHeader label="KEY" sortKey="key" currentKey={props.currentSortKey} direction={props.currentSortDirection} onClick={handleSort} />
                </div>

                <div className="space-y-1">
                    {filteredFiles.map(file => (
                        <div key={file.id} onClick={() => setActiveTrackId(file.id)}>
                            <FileListItem 
                                file={file} 
                                onProcess={props.onProcessFile}
                                onEdit={(f) => props.onSingleItemEdit(f.id)}
                                onDelete={props.onDeleteItem}
                                onSelectionChange={props.onSelectionChange}
                                isPlaying={props.playingFileId === file.id && props.isPlaying}
                                onPlayPause={() => props.onPlayPause(file.id)}
                                isActive={activeTrackId === file.id}
                                onInspect={() => props.onInspectItem(file.id)}
                                onToggleFavorite={props.onToggleFavorite}
                                onAddToPlaylist={props.onAddToPlaylist}
                                gridClass={gridTemplate}
                            />
                        </div>
                    ))}
                </div>
            </div>
        </div>

        {/* --- RIGHT PANEL (Active Track Inspector) --- */}
        {activeTrack && (
            <div className="hidden lg:flex w-[380px] flex-shrink-0 bg-[#0a0a0f] flex-col border-l border-white/5 p-6 relative overflow-hidden">
                {/* Glow Background */}
                <div className="absolute top-[-10%] right-[-20%] w-[300px] h-[300px] bg-indigo-600/20 rounded-full blur-[80px] pointer-events-none"></div>
                <div className="absolute bottom-[10%] left-[-10%] w-[250px] h-[250px] bg-fuchsia-600/10 rounded-full blur-[80px] pointer-events-none"></div>

                {/* Cover Art - BIG */}
                <div className="relative aspect-square w-full mb-6 group">
                    <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500 to-fuchsia-500 rounded-3xl blur opacity-30 group-hover:opacity-50 transition-opacity duration-500"></div>
                    <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-white/10 w-full h-full">
                        <AlbumCover tags={activeTags} className="w-full h-full object-cover" />
                        {/* Play Overlay */}
                        <button 
                            onClick={() => props.onPlayPause(activeTrack.id)}
                            className="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/40 transition-colors cursor-pointer"
                        >
                            <div className="w-16 h-16 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-white shadow-lg transform group-hover:scale-110 transition-transform">
                                {props.isPlaying && props.playingFileId === activeTrack.id ? (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                                ) : (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 pl-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                                )}
                            </div>
                        </button>
                    </div>
                </div>

                {/* Track Info */}
                <div className="mb-6 relative z-10">
                    <h2 className="text-2xl font-bold text-white leading-tight mb-1 neon-text-pink truncate" title={activeTags?.title || activeTrack.file.name}>
                        {activeTags?.title || activeTrack.file.name}
                    </h2>
                    <p className="text-lg text-slate-400 font-medium truncate" title={activeTags?.artist}>
                        {activeTags?.artist || 'Unknown Artist'}
                    </p>
                    <div className="flex gap-2 mt-2 text-sm text-slate-500">
                        <span>{activeTags?.album || 'Unknown Album'}</span>
                        <span>•</span>
                        <span>{activeTags?.year || '????'}</span>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3 mb-8 relative z-10">
                    <div className="bg-white/5 p-3 rounded-xl border border-white/5">
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">BPM</p>
                        <p className="text-xl font-mono text-cyan-400 font-bold">{activeTags?.bpm || '-'}</p>
                    </div>
                    <div className="bg-white/5 p-3 rounded-xl border border-white/5">
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">KEY</p>
                        <p className="text-xl font-mono text-fuchsia-400 font-bold">{activeTags?.initialKey || '-'}</p>
                    </div>
                </div>

                {/* Actions */}
                <div className="grid grid-cols-2 gap-3 mt-auto relative z-10">
                    <button 
                        onClick={() => props.onSingleItemEdit(activeTrack.id)}
                        className="py-3 px-4 rounded-xl border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10 font-bold text-sm transition-colors uppercase tracking-wider"
                    >
                        EDYTUJ TAGI
                    </button>
                    <button 
                        onClick={() => props.onInspectItem(activeTrack.id)}
                        className="py-3 px-4 rounded-xl border border-white/10 text-slate-300 hover:bg-white/5 font-bold text-sm transition-colors uppercase tracking-wider"
                    >
                        SZCZEGÓŁY
                    </button>
                    <button 
                        onClick={() => props.onAddToPlaylist(activeTrack.id)}
                        className="col-span-2 py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-fuchsia-600 hover:from-indigo-500 hover:to-fuchsia-500 text-white font-bold text-sm transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] uppercase tracking-wider"
                    >
                        DODAJ DO PLAYLISTY
                    </button>
                </div>
            </div>
        )}
    </div>
  );
};

export default LibraryTab;
