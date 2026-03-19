
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { AudioFile, ProcessingState, ID3Tags, Playlist } from '../types';
import { sortFiles, SortConfig } from '../utils/sortingUtils';
import { generatePath } from '../utils/filenameUtils';
import { readID3Tags } from '../utils/audioUtils';

export interface LibraryFilters {
  search: string;
  bpmMin?: number;
  bpmMax?: number;
  genre?: string;
  key?: string;
  playlistId?: string | null;
}

// Helper types for serialization
interface SerializableAudioFile {
  id: string;
  state: ProcessingState;
  originalTags: ID3Tags;
  fetchedTags?: ID3Tags;
  newName?: string;
  isSelected?: boolean;
  errorMessage?: string;
  dateAdded: number;
  webkitRelativePath?: string;
  fileName: string;
  fileType: string;
  duplicateSetId?: string;
}

declare const uuid: { v4: () => string; };
const SUPPORTED_FORMATS = ['audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/flac', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/x-m4a', 'audio/aac', 'audio/x-ms-wma'];

export const useLibrary = (renamePattern: string) => {
  // --- Files State ---
  const [files, setFiles] = useState<AudioFile[]>(() => {
    const saved = localStorage.getItem('audioFiles');
    if (saved) {
      try {
        const parsed: SerializableAudioFile[] = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed.map(f => ({
            ...f,
            file: new File([], f.fileName, { type: f.fileType }), // Empty file blob as placeholder
            handle: null,
          }));
        }
      } catch (e) {
        console.error("Failed to parse audio files", e);
        localStorage.removeItem('audioFiles');
      }
    }
    return [];
  });

  const [playlists, setPlaylists] = useState<Playlist[]>(() => {
      const saved = localStorage.getItem('playlists');
      return saved ? JSON.parse(saved) : [];
  });

  const [isRestored, setIsRestored] = useState(false);
  const isRestoredRef = useRef(false);

  // --- Selection & View State ---
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<SortConfig[]>([]);
  
  // --- Filters & Pagination ---
  const [filters, setFilters] = useState<LibraryFilters>({ search: '' });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);

  // --- Effects ---
  
  // Reset page when filters change
  useEffect(() => {
      setCurrentPage(1);
  }, [filters, sortConfig, files.length]);

  // Mark as restored on initial load
  useEffect(() => {
    if (files.length > 0 && !isRestored && !isRestoredRef.current) {
        isRestoredRef.current = true;
        setIsRestored(true);
    }
  }, [files]);

  // Persist Files
  useEffect(() => {
    if (files.length === 0 && !isRestored) {
        localStorage.removeItem('audioFiles');
        return;
    }
    if (files.length > 0) {
        const serializableFiles: SerializableAudioFile[] = files.map(f => ({
            id: f.id,
            state: f.state,
            originalTags: f.originalTags,
            fetchedTags: f.fetchedTags,
            newName: f.newName,
            isSelected: f.isSelected, 
            errorMessage: f.errorMessage,
            dateAdded: f.dateAdded,
            webkitRelativePath: f.webkitRelativePath,
            fileName: f.file.name,
            fileType: f.file.type,
            duplicateSetId: f.duplicateSetId,
        }));
        localStorage.setItem('audioFiles', JSON.stringify(serializableFiles));
    }
  }, [files, isRestored]);

  // Persist Playlists
  useEffect(() => {
      localStorage.setItem('playlists', JSON.stringify(playlists));
  }, [playlists]);

  // Apply Rename Pattern
  useEffect(() => {
    setFiles(currentFiles => 
        currentFiles.map(file => {
            const tagsToUse = file.fetchedTags || file.originalTags;
            const newName = generatePath(renamePattern, tagsToUse, file.file.name);
            if (file.newName === newName) return file;
            return { ...file, newName };
        })
    );
  }, [renamePattern]);


  // --- Actions ---

  const addFiles = useCallback(async (newFilesData: { file: File, handle?: any, path?: string }[]) => {
    if (typeof uuid === 'undefined') return;
    const validAudioFiles = newFilesData.filter(item => SUPPORTED_FORMATS.includes(item.file.type));
    if (validAudioFiles.length === 0) return;

    setIsRestored(false); 
    isRestoredRef.current = false;

    const newAudioFiles: AudioFile[] = await Promise.all(
        validAudioFiles.map(async item => {
            const originalTags = await readID3Tags(item.file);
            return {
                id: uuid.v4(),
                file: item.file,
                handle: item.handle,
                webkitRelativePath: item.path || item.file.webkitRelativePath,
                state: ProcessingState.PENDING,
                originalTags,
                dateAdded: Date.now(),
                isSelected: false
            };
        })
    );

    setFiles(prev => [...prev, ...newAudioFiles]);
  }, []);

  const updateFile = useCallback((id: string, updates: Partial<AudioFile>) => {
    setFiles(prevFiles => prevFiles.map(f => f.id === id ? { ...f, ...updates } : f));
  }, []);

  const removeFiles = useCallback((idsToRemove: string[]) => {
      setFiles(prev => prev.filter(f => !idsToRemove.includes(f.id)));
      setSelectedFileIds(prev => prev.filter(id => !idsToRemove.includes(id)));
      if (activeFileId && idsToRemove.includes(activeFileId)) {
          setActiveFileId(null);
      }
      // Remove from playlists as well
      setPlaylists(prev => prev.map(pl => ({
          ...pl,
          trackIds: pl.trackIds.filter(tid => !idsToRemove.includes(tid))
      })));
  }, [activeFileId]);

  const toggleSelection = useCallback((id: string, multi: boolean) => {
    if (multi) {
        setSelectedFileIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
    } else {
        setSelectedFileIds(prev => prev.includes(id) && prev.length === 1 ? [] : [id]);
    }
    setActiveFileId(id);
  }, []);

  const selectAll = useCallback(() => {
      // NOTE: This now selects ALL filtered files, not just the current page
      setSelectedFileIds(sortedFiles.map(f => f.id));
  }, []); 

  const clearSelection = useCallback(() => {
      setSelectedFileIds([]);
  }, []);

  const activateFile = useCallback((file: AudioFile) => {
      setActiveFileId(file.id);
  }, []);

  // --- Playlist Actions ---
  
  const createPlaylist = useCallback((name: string, initialTrackIds: string[] = []) => {
      if (typeof uuid === 'undefined') return;
      const newPlaylist: Playlist = {
          id: uuid.v4(),
          name,
          trackIds: initialTrackIds,
          createdAt: Date.now()
      };
      setPlaylists(prev => [...prev, newPlaylist]);
  }, []);

  const deletePlaylist = useCallback((id: string) => {
      setPlaylists(prev => prev.filter(p => p.id !== id));
      if (filters.playlistId === id) {
          setFilters(prev => ({ ...prev, playlistId: null }));
      }
  }, [filters.playlistId]);

  const addToPlaylist = useCallback((playlistId: string, fileIds: string[]) => {
      setPlaylists(prev => prev.map(pl => {
          if (pl.id === playlistId) {
              const newIds = Array.from(new Set([...pl.trackIds, ...fileIds]));
              return { ...pl, trackIds: newIds };
          }
          return pl;
      }));
  }, []);

  // --- Derived State ---
  
  const filteredFiles = useMemo(() => {
      return files.filter(f => {
          // Playlist Filter
          if (filters.playlistId) {
              const playlist = playlists.find(p => p.id === filters.playlistId);
              if (!playlist || !playlist.trackIds.includes(f.id)) return false;
          }

          const tags = f.fetchedTags || f.originalTags;
          
          // Search
          if (filters.search) {
              const q = filters.search.toLowerCase();
              const match = 
                  f.file.name.toLowerCase().includes(q) ||
                  tags.artist?.toLowerCase().includes(q) ||
                  tags.title?.toLowerCase().includes(q) ||
                  tags.album?.toLowerCase().includes(q);
              if (!match) return false;
          }

          // BPM
          const bpm = typeof tags.bpm === 'string' ? parseFloat(tags.bpm) : tags.bpm;
          if (filters.bpmMin !== undefined && (!bpm || bpm < filters.bpmMin)) return false;
          if (filters.bpmMax !== undefined && (!bpm || bpm > filters.bpmMax)) return false;

          // Genre
          if (filters.genre && tags.genre?.toLowerCase() !== filters.genre.toLowerCase()) return false;

          // Key
          if (filters.key && !tags.initialKey?.toLowerCase().includes(filters.key.toLowerCase())) return false;

          return true;
      });
  }, [files, filters, playlists]);

  const sortedFiles = useMemo(() => sortFiles(filteredFiles, sortConfig), [filteredFiles, sortConfig]);
  
  const paginatedFiles = useMemo(() => {
      const start = (currentPage - 1) * itemsPerPage;
      return sortedFiles.slice(start, start + itemsPerPage);
  }, [sortedFiles, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(sortedFiles.length / itemsPerPage);

  const activeFile = useMemo(() => files.find(f => f.id === activeFileId) || null, [files, activeFileId]);
  
  const selectedFiles = useMemo(() => files.filter(f => selectedFileIds.includes(f.id)), [files, selectedFileIds]);

  const availableGenres = useMemo(() => {
      const genres = new Set<string>();
      files.forEach(f => {
          const g = f.fetchedTags?.genre || f.originalTags.genre;
          if (g) genres.add(g);
      });
      return Array.from(genres).sort();
  }, [files]);

  return {
    files,
    setFiles,
    sortedFiles, // All filtered files (for stats/operations)
    paginatedFiles, // Just current page (for display)
    totalPages,
    currentPage,
    setCurrentPage,
    itemsPerPage,
    setItemsPerPage,
    
    selectedFileIds,
    activeFileId,
    activeFile,
    selectedFiles,
    isRestored,
    sortConfig,
    setSortConfig,
    addFiles,
    updateFile,
    removeFiles,
    toggleSelection,
    selectAll: () => setSelectedFileIds(sortedFiles.map(f => f.id)),
    clearSelection,
    activateFile,
    setIsRestored, 
    setDirectoryHandle: (handle: any) => {},
    
    // Filter props
    filters,
    setFilters,
    availableGenres,

    // Playlist props
    playlists,
    createPlaylist,
    deletePlaylist,
    addToPlaylist
  };
};
