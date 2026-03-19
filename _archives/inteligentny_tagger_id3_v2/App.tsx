import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';

// Components
import WelcomeScreen from './components/WelcomeScreen';
import FileListItem from './components/FileListItem';
import Footer from './components/Footer';
import SettingsModal from './components/SettingsModal';
import EditTagsModal from './components/EditTagsModal';
import RenameModal from './components/RenameModal';
import ConfirmationModal from './components/ConfirmationModal';
import BatchEditModal from './components/BatchEditModal';
import PostDownloadModal from './components/PostDownloadModal';
import AlbumCoverModal from './components/AlbumCoverModal';
import HeaderToolbar from './components/HeaderToolbar';
import PreviewChangesModal from './components/PreviewChangesModal';
import DuplicateFinderModal from './components/DuplicateFinderModal';
import XmlConverterModal from './components/XmlConverterModal';
import SmartCollectionModal from './components/SmartCollectionModal';
import TrackInfoPanel from './components/TrackInfoPanel';
import Sidebar from './components/Sidebar';
import FileDropzone from './components/FileDropzone';
import BatchActionsToolbar from './components/BatchActionsToolbar';
import EmptyState from './components/EmptyState';
import TrackContextMenu from './components/TrackContextMenu';
import { sortPlaylistIntelligently } from './utils/playlistIntelligenceUtils'; 
import { exportPlaylistToRekordboxXml, exportPlaylistToVirtualDjXml } from './utils/xmlUtils'; 

// Types
import { AudioFile, ProcessingState, ID3Tags, SmartCollection, Hotcue, Playlist } from './types';
import { AIProvider, ApiKeys, fetchTagsForFile, fetchTagsForBatch } from './services/geminiService';

// Utils
import { readID3Tags, applyTags, saveFileDirectly } from './utils/audioUtils';
import { generatePath } from './utils/filenameUtils';
import { sortFiles, SortKey } from './utils/sortingUtils';
import { exportFilesToCsv } from './utils/csvUtils';
import { filterFilesByRules } from './utils/collectionUtils';
import { handleTrackReorder } from './utils/playlistUtils';

declare const uuid: { v4: () => string; };
declare const JSZip: any;
declare const saveAs: any;

const SUPPORTED_FORMATS = ['audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/flac', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/x-m4a', 'audio/aac'];

interface RenamePreview { originalName: string; newName: string; isTooLong: boolean; }
type ModalState = | { type: 'none' } | { type: 'edit'; fileId: string } | { type: 'rename' } | { type: 'delete'; fileId: string | 'selected' | 'all' } | { type: 'settings' } | { type: 'batch-edit' } | { type: 'post-download'; count: number } | { type: 'zoom-cover', imageUrl: string } | { type: 'preview-changes'; title: string; confirmationText: string; previews: RenamePreview[]; onConfirm: () => void; } | { type: 'find-duplicates' } | { type: 'xml-converter' } | { type: 'smart-collection' };

async function* getFilesRecursively(entry: any): AsyncGenerator<{ file: File, handle: any, path: string }> {
    if (entry.kind === 'file') {
        const file = await entry.getFile();
        if (SUPPORTED_FORMATS.includes(file.type)) {
            yield { file, handle: entry, path: entry.name };
        }
    } else if (entry.kind === 'directory') {
        for await (const handle of entry.values()) {
            for await (const nestedFile of getFilesRecursively(handle)) {
                 yield { ...nestedFile, path: `${entry.name}/${nestedFile.path}` };
            }
        }
    }
}

const getAudioDuration = (file: File): Promise<number> => {
    return new Promise((resolve) => {
        const audio = document.createElement('audio');
        audio.preload = 'metadata';
        audio.onloadedmetadata = () => {
            window.URL.revokeObjectURL(audio.src);
            resolve(audio.duration);
        };
        audio.onerror = () => {
            window.URL.revokeObjectURL(audio.src);
            console.warn(`Could not read duration for ${file.name}`);
            resolve(0);
        };
        audio.src = window.URL.createObjectURL(file);
    });
};

const App: React.FC = () => {
    const [files, setFiles] = useState<AudioFile[]>([]);
    const [playlists, setPlaylists] = useState<Playlist[]>(() => JSON.parse(localStorage.getItem('playlists') || '[]'));
    const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
    const lastSelectedIdRef = useRef<string | null>(null);
    const [isBatchAnalyzing, setIsBatchAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [savingFileId, setSavingFileId] = useState<string | null>(null);
    const [directoryHandle, setDirectoryHandle] = useState<any | null>(null);
    
    const [theme, setTheme] = useState<'light' | 'dark'>(() => (localStorage.getItem('theme') as 'light' | 'dark') || 'dark');
    const [apiKeys, setApiKeys] = useState<ApiKeys>(() => JSON.parse(localStorage.getItem('apiKeys') || '{"grok":"","openai":""}'));
    const [aiProvider, setAiProvider] = useState<AIProvider>(() => (localStorage.getItem('aiProvider') as AIProvider) || 'gemini');
    const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: 'asc' | 'desc' }>(() => ({
      key: (localStorage.getItem('sortKey') as SortKey) || 'dateAdded',
      direction: (localStorage.getItem('sortDirection') as 'asc' | 'desc') || 'asc'
    }));
    const [renamePattern, setRenamePattern] = useState<string>(() => localStorage.getItem('renamePattern') || '[artist] - [title]');
    const [smartCollections, setSmartCollections] = useState<SmartCollection[]>(() => JSON.parse(localStorage.getItem('smartCollections') || '[]'));
    const [activeView, setActiveView] = useState<{ type: 'all' | 'collection' | 'playlist', id: string | null }>({ type: 'all', id: null });
    const [modalState, setModalState] = useState<ModalState>({ type: 'none' });
    const [contextMenu, setContextMenu] = useState<{ x: number, y: number, file: AudioFile } | null>(null);


    useEffect(() => { localStorage.setItem('theme', theme); document.documentElement.className = theme; }, [theme]);
    useEffect(() => { localStorage.setItem('apiKeys', JSON.stringify(apiKeys)); }, [apiKeys]);
    useEffect(() => { localStorage.setItem('aiProvider', aiProvider); }, [aiProvider]);
    useEffect(() => { localStorage.setItem('sortKey', sortConfig.key); localStorage.setItem('sortDirection', sortConfig.direction); }, [sortConfig]);
    useEffect(() => { localStorage.setItem('renamePattern', renamePattern); }, [renamePattern]);
    useEffect(() => { localStorage.setItem('smartCollections', JSON.stringify(smartCollections)); }, [smartCollections]);
    useEffect(() => { localStorage.setItem('playlists', JSON.stringify(playlists)); }, [playlists]);

    useEffect(() => {
        setFiles(currentFiles => 
            currentFiles.map(file => {
                const tagsToUse = file.fetchedTags || file.originalTags;
                const newName = generatePath(renamePattern, tagsToUse, file.file.name);
                return { ...file, newName };
            })
        );
    }, [renamePattern, files.length]);
    
     useEffect(() => {
        const closeContextMenu = () => setContextMenu(null);
        window.addEventListener('click', closeContextMenu);
        return () => window.removeEventListener('click', closeContextMenu);
    }, []);

    const updateFileState = useCallback((id: string, updates: Partial<AudioFile>) => {
        setFiles(prevFiles => prevFiles.map(f => f.id === id ? { ...f, ...updates } : f));
    }, []);

    const handleClearAndReset = () => { setFiles([]); setDirectoryHandle(null); setSelectedFileId(null); setActiveView({ type: 'all', id: null }); };

    const addFilesToQueue = useCallback(async (filesToAdd: { file: File, handle?: any, path?: string }[]) => {
        if (typeof uuid === 'undefined') { alert("Błąd krytyczny: Biblioteka 'uuid' nie została załadowana."); return; }
        const validAudioFiles = filesToAdd.filter(item => SUPPORTED_FORMATS.includes(item.file.type));
        if (validAudioFiles.length === 0) throw new Error(`Żaden z podanych plików nie jest obsługiwanym formatem audio.`);
    
        const newAudioFiles: AudioFile[] = await Promise.all(
            validAudioFiles.map(async item => {
                const { tags, hotcues } = await readID3Tags(item.file);
                const duration = await getAudioDuration(item.file);
                return {
                    id: uuid.v4(),
                    file: item.file,
                    handle: item.handle,
                    webkitRelativePath: item.path || item.file.webkitRelativePath,
                    state: ProcessingState.PENDING,
                    originalTags: tags,
                    dateAdded: Date.now(),
                    hotcues: hotcues,
                    duration: duration,
                };
            })
        );
        setFiles(prev => [...prev, ...newAudioFiles]);
    }, []);
    
    const handleUrlSubmitted = useCallback(async (url: string) => {
        try {
            const proxiedUrl = `https://corsproxy.io/?${encodeURIComponent(url)}`;
            const response = await fetch(proxiedUrl);
            if (!response.ok) {
                throw new Error(`Nie udało się pobrać pliku z URL: ${response.statusText}`);
            }
            const blob = await response.blob();
            
            let filename = "downloaded_audio_file";
             try {
                const urlPath = new URL(url).pathname;
                const lastSegment = urlPath.substring(urlPath.lastIndexOf('/') + 1);
                if (lastSegment) {
                    filename = decodeURIComponent(lastSegment);
                }
            } catch (e) { /* Invalid URL, fallback is fine */ }

            const file = new File([blob], filename, { type: blob.type });

            if (!SUPPORTED_FORMATS.includes(file.type)) {
                throw new Error(`Typ pliku '${file.type}' z podanego adresu URL nie jest obsługiwany.`);
            }

            await addFilesToQueue([{ file }]);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "Wystąpił nieznany błąd.";
            alert(`Błąd podczas przetwarzania URL: ${errorMessage}`);
            throw error;
        }
    }, [addFilesToQueue]);

    const handleFilesSelected = useCallback(async (selectedFiles: FileList) => {
        try {
             const fileList = Array.from(selectedFiles).map(f => ({ file: f }));
            await addFilesToQueue(fileList);
        } catch (error) {
            alert(`Błąd: ${error instanceof Error ? error.message : "Wystąpił nieznany błąd."}`);
        }
    }, [addFilesToQueue]);

    const handleDirectoryConnect = useCallback(async (handle: any) => {
        handleClearAndReset();
        setDirectoryHandle(handle);
        try {
            const filesToProcess: { file: File, handle: any, path: string }[] = [];
            for await (const fileData of getFilesRecursively(handle)) {
                filesToProcess.push(fileData);
            }
            await addFilesToQueue(filesToProcess);
        } catch (error) {
            alert(`Błąd: ${error instanceof Error ? error.message : "Wystąpił nieznany błąd."}`);
            setDirectoryHandle(null);
        }
    }, [addFilesToQueue]);
    
    const displayedFiles = useMemo(() => {
        let filesToDisplay: AudioFile[] = [];
        if (activeView.type === 'all') {
            filesToDisplay = files;
        } else if (activeView.type === 'collection') {
            const collection = smartCollections.find(c => c.id === activeView.id);
            if (collection) filesToDisplay = filterFilesByRules(files, collection);
        } else if (activeView.type === 'playlist') {
            const playlist = playlists.find(p => p.id === activeView.id);
            if (playlist) {
                const fileMap = new Map(files.map(f => [f.id, f]));
                filesToDisplay = playlist.trackIds.map(id => fileMap.get(id)).filter((f): f is AudioFile => !!f);
            }
        }
        return activeView.type === 'playlist' ? filesToDisplay : sortFiles([...filesToDisplay], sortConfig.key, sortConfig.direction);
    }, [files, sortConfig, activeView, smartCollections, playlists]);
    
    const selectedFile = useMemo(() => files.find(f => f.id === selectedFileId), [files, selectedFileId]);
    const activeViewDetails = useMemo(() => {
        if (activeView.type === 'collection') return smartCollections.find(c => c.id === activeView.id);
        if (activeView.type === 'playlist') return playlists.find(p => p.id === activeView.id);
        return null;
    }, [smartCollections, playlists, activeView]);

    const selectedFiles = useMemo(() => files.filter(f => f.isSelected), [files]);
    const allDisplayedFilesSelected = useMemo(() => displayedFiles.length > 0 && displayedFiles.every(f => f.isSelected), [displayedFiles]);
    const isProcessing = useMemo(() => files.some(f => f.state === ProcessingState.PROCESSING || f.state === ProcessingState.DOWNLOADING), [files]);
    const modalFile = useMemo(() => (modalState.type === 'edit' ? files.find(f => f.id === modalState.fileId) : undefined), [modalState, files]);

    const handleSelectionChange = (fileId: string, isSelected: boolean) => {
        setFiles(prevFiles => prevFiles.map(f => f.id === fileId ? { ...f, isSelected } : f));
    };

    const handleSelect = (file: AudioFile, e: React.MouseEvent) => {
        setSelectedFileId(file.id);
        if (e.shiftKey && lastSelectedIdRef.current) {
            const lastIndex = displayedFiles.findIndex(f => f.id === lastSelectedIdRef.current);
            const currentIndex = displayedFiles.findIndex(f => f.id === file.id);
            if (lastIndex !== -1 && currentIndex !== -1) {
                const start = Math.min(lastIndex, currentIndex);
                const end = Math.max(lastIndex, currentIndex);
                const idsToSelect = displayedFiles.slice(start, end + 1).map(f => f.id);
                setFiles(prev => prev.map(f => idsToSelect.includes(f.id) ? { ...f, isSelected: true } : f));
            }
        } else if (e.ctrlKey || e.metaKey) {
            handleSelectionChange(file.id, !file.isSelected);
        } else {
            setFiles(prev => prev.map(f => ({ ...f, isSelected: f.id === file.id })));
        }
        lastSelectedIdRef.current = file.id;
    };
    
    const handleToggleSelectAll = () => {
        const shouldSelectAll = !allDisplayedFilesSelected;
        const displayedFileIds = new Set(displayedFiles.map(f => f.id));
        setFiles(prev => prev.map(f => displayedFileIds.has(f.id) ? { ...f, isSelected: shouldSelectAll } : f));
    };

    const handleClearSelection = () => setFiles(prev => prev.map(f => ({...f, isSelected: false})));
    const handleDeleteFiles = (fileIds: string[]) => setFiles(current => current.filter(f => !fileIds.includes(f.id)));
    const handleSaveTags = (fileId: string, tags: ID3Tags) => { updateFileState(fileId, { fetchedTags: tags }); setModalState({ type: 'none' }); };
    
    const applyChangesToFile = async (fileId: string, newTags?: ID3Tags, newHotcues?: Hotcue[]) => {
        if (!directoryHandle) return;
        const fileToSave = files.find(f => f.id === fileId);
        if (!fileToSave) return;

        setSavingFileId(fileId);
        const fileWithChanges = { ...fileToSave, fetchedTags: newTags ?? fileToSave.fetchedTags, hotcues: newHotcues ?? fileToSave.hotcues };
        const result = await saveFileDirectly(directoryHandle, fileWithChanges);
        if (result.success && result.updatedFile) {
            updateFileState(fileId, result.updatedFile);
        } else {
            alert(`Nie udało się zapisać pliku ${fileToSave.file.name}: ${result.errorMessage}`);
        }
        setSavingFileId(null);
    };
    
    const handleApplyTags = (fileId: string, tags: ID3Tags) => applyChangesToFile(fileId, tags, undefined);

    const handleSetHotcue = (fileId: string, hotcue: Hotcue) => {
        let updatedHotcues: Hotcue[] = [];
        setFiles(prevFiles => prevFiles.map(f => {
            if (f.id === fileId) {
                const existingCues = f.hotcues.filter(c => c.num !== hotcue.num);
                updatedHotcues = [...existingCues, hotcue].sort((a, b) => a.num - b.num);
                return { ...f, hotcues: updatedHotcues };
            }
            return f;
        }));
        if (directoryHandle) {
            applyChangesToFile(fileId, undefined, updatedHotcues);
        }
    };
    
    const handleProcessFile = async (file: AudioFile) => {
        if(file.state === ProcessingState.PROCESSING || file.state === ProcessingState.DOWNLOADING) return;
        updateFileState(file.id, { state: ProcessingState.PROCESSING, errorMessage: undefined });
        try {
            const fetchedTags = await fetchTagsForFile(file.file.name, file.originalTags, aiProvider, apiKeys);
            updateFileState(file.id, { fetchedTags: fetchedTags, state: ProcessingState.SUCCESS });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "Wystąpił nieznany błąd.";
            updateFileState(file.id, { state: ProcessingState.ERROR, errorMessage });
        }
    };
    
    // --- Playlist Handlers ---
    const handleCreatePlaylist = () => setPlaylists([...playlists, { id: uuid.v4(), name: `Nowa Playlista ${playlists.length + 1}`, trackIds: [] }]);
    const handleRenamePlaylist = (id: string, newName: string) => setPlaylists(playlists.map(p => p.id === id ? { ...p, name: newName } : p));
    const handleDeletePlaylist = (id: string) => { setPlaylists(playlists.filter(p => p.id !== id)); if (activeView.id === id) setActiveView({ type: 'all', id: null }); };
    const handleAddTracksToPlaylist = (playlistId: string, trackIds: string[]) => {
        setPlaylists(playlists.map(p => {
            if (p.id === playlistId) {
                const newTrackIds = trackIds.filter(id => !p.trackIds.includes(id));
                return { ...p, trackIds: [...p.trackIds, ...newTrackIds] };
            }
            return p;
        }));
    };
    const handleRemoveTrackFromPlaylist = (playlistId: string, trackId: string) => {
        setPlaylists(playlists.map(p => p.id === playlistId ? { ...p, trackIds: p.trackIds.filter(id => id !== trackId) } : p));
    };
    const handleReorderPlaylist = (playlistId: string, oldIndex: number, newIndex: number) => setPlaylists(playlists.map(p => p.id === playlistId ? { ...p, trackIds: handleTrackReorder(p.trackIds, oldIndex, newIndex) } : p));
    
    const handleIntelliSortPlaylist = (playlistId: string) => {
        const playlist = playlists.find(p => p.id === playlistId);
        if (!playlist) return;
        const playlistFiles = playlist.trackIds.map(id => files.find(f => f.id === id)).filter((f): f is AudioFile => !!f);
        const sortedFiles = sortPlaylistIntelligently(playlistFiles);
        const sortedIds = sortedFiles.map(f => f.id);
        setPlaylists(playlists.map(p => p.id === playlistId ? { ...p, trackIds: sortedIds } : p));
    };

    const handleExportPlaylist = (playlistId: string, format: 'rekordbox' | 'virtualdj') => {
        const playlist = playlists.find(p => p.id === playlistId);
        if (!playlist) return;
        const playlistFiles = playlist.trackIds.map(id => files.find(f => f.id === id)).filter((f): f is AudioFile => !!f);
        
        try {
            let xmlString;
            let filename;

            if (format === 'rekordbox') {
                xmlString = exportPlaylistToRekordboxXml(playlistFiles, playlist.name);
                filename = `${playlist.name}_rekordbox.xml`;
            } else {
                xmlString = exportPlaylistToVirtualDjXml(playlistFiles, playlist.name);
                filename = `${playlist.name}_virtualdj.xml`;
            }

            const blob = new Blob([xmlString], { type: 'application/xml;charset=utf-8' });
            saveAs(blob, filename);
        } catch (error) {
            alert(`Błąd podczas eksportu playlisty: ${error instanceof Error ? error.message : 'Nieznany błąd'}`);
        }
    };
    
    const handleBatchAnalyze = useCallback(async (filesToAnalyze: AudioFile[]) => {
        const pendingFiles = filesToAnalyze.filter(f => f.state === ProcessingState.PENDING || f.state === ProcessingState.ERROR);
        if (pendingFiles.length === 0) return;

        setIsBatchAnalyzing(true);
        pendingFiles.forEach(file => updateFileState(file.id, { state: ProcessingState.PROCESSING }));

        try {
            const results = await fetchTagsForBatch(pendingFiles, aiProvider, apiKeys);
            const processedFilenames = new Set<string>();

            results.forEach(result => {
                const fileToUpdate = pendingFiles.find(f => f.file.name === result.originalFilename);
                if (fileToUpdate) {
                    const mergedTags: ID3Tags = { ...fileToUpdate.originalTags, ...result };
                    delete (mergedTags as any).originalFilename;
                    updateFileState(fileToUpdate.id, {
                        fetchedTags: mergedTags,
                        state: ProcessingState.SUCCESS,
                    });
                    processedFilenames.add(result.originalFilename);
                }
            });
            
            pendingFiles.forEach(file => {
                if (!processedFilenames.has(file.file.name)) {
                     updateFileState(file.id, {
                        state: ProcessingState.ERROR,
                        errorMessage: "AI nie zwróciło wyników dla tego pliku w trybie wsadowym.",
                    });
                }
            });

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "Wystąpił nieznany błąd podczas analizy wsadowej.";
            alert(`Błąd: ${errorMessage}`);
            pendingFiles.forEach(file => updateFileState(file.id, {
                state: ProcessingState.ERROR,
                errorMessage,
            }));
        } finally {
            setIsBatchAnalyzing(false);
        }
    }, [aiProvider, apiKeys, updateFileState]);

    const handleDownloadOrSave = async (filesToProcess: AudioFile[]) => {
        if (filesToProcess.length === 0) return;
        
        setIsSaving(true);
        
        if (directoryHandle) {
            for (const file of filesToProcess) {
                updateFileState(file.id, { state: ProcessingState.DOWNLOADING });
                const result = await saveFileDirectly(directoryHandle, file);
                 if (result.success && result.updatedFile) {
                    updateFileState(file.id, { ...result.updatedFile, state: ProcessingState.SUCCESS, isSelected: false });
                } else {
                    updateFileState(file.id, { state: ProcessingState.ERROR, errorMessage: result.errorMessage });
                }
            }
        } else {
             if (typeof JSZip === 'undefined' || typeof saveAs === 'undefined') {
                alert("Błąd krytyczny: Biblioteki 'JSZip' lub 'FileSaver' nie zostały załadowane.");
                setIsSaving(false);
                return;
            }
            const zip = new JSZip();
            for (const file of filesToProcess) {
                 updateFileState(file.id, { state: ProcessingState.DOWNLOADING });
                try {
                    const blob = await applyTags(file.file, file.fetchedTags || file.originalTags, file.hotcues);
                    zip.file(file.newName || file.file.name, blob);
                    updateFileState(file.id, { state: ProcessingState.SUCCESS, isSelected: false });
                } catch(e) {
                     updateFileState(file.id, { state: ProcessingState.ERROR, errorMessage: e instanceof Error ? e.message : 'Błąd zapisu tagów.' });
                }
            }
            try {
                const content = await zip.generateAsync({ type: 'blob' });
                saveAs(content, 'tagged-files.zip');
                setModalState({ type: 'post-download', count: filesToProcess.length });
            } catch (zipError) {
                 alert(`Błąd podczas tworzenia archiwum ZIP: ${zipError instanceof Error ? zipError.message : "Nieznany błąd"}`);
            }
        }
        setIsSaving(false);
    };

    const handleExportCsv = () => {
        if (selectedFiles.length === 0) {
            alert("Zaznacz pliki, które chcesz wyeksportować.");
            return;
        }
        try {
            const csv = exportFilesToCsv(selectedFiles);
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            saveAs(blob, 'file_tags_export.csv');
        } catch (error) {
             alert(`Błąd podczas eksportu do CSV: ${error instanceof Error ? error.message : "Nieznany błąd"}`);
        }
    };
    
    const handleSaveSmartCollection = (collection: SmartCollection) => {
        setSmartCollections(prev => {
            const existing = prev.find(c => c.id === collection.id);
            if (existing) {
                return prev.map(c => c.id === collection.id ? collection : c);
            }
            return [...prev, collection];
        });
        setModalState({ type: 'none' });
    };

    const handleSaveBatchEdit = (tagsToApply: Partial<ID3Tags>) => {
        setFiles(prev => prev.map(f => {
            if(f.isSelected) {
                const newTags = { ...(f.fetchedTags || f.originalTags), ...tagsToApply };
                return { ...f, fetchedTags: newTags };
            }
            return f;
        }));
        setModalState({ type: 'none' });
    };

    const handleSaveRename = (newPattern: string) => {
        const previews = selectedFiles.map(file => {
            const newName = generatePath(newPattern, file.fetchedTags || file.originalTags, file.file.name);
            return { originalName: file.webkitRelativePath || file.file.name, newName, isTooLong: newName.length > 255 };
        });

        setModalState({ 
            type: 'preview-changes',
            title: `Potwierdź zmianę ${selectedFiles.length} nazw`,
            confirmationText: `Czy na pewno chcesz zmienić nazwy ${selectedFiles.length} plików zgodnie z szablonem "${newPattern}"?`,
            previews,
            onConfirm: () => {
                setRenamePattern(newPattern);
                setFiles(prev => prev.map(f => {
                    if (f.isSelected) {
                        const newName = generatePath(newPattern, f.fetchedTags || f.originalTags, f.file.name);
                        return { ...f, newName };
                    }
                    return f;
                }));
                setModalState({ type: 'none' });
            }
        });
    };
    
    const handleNextTrack = useCallback(() => {
        const currentIndex = displayedFiles.findIndex(f => f.id === selectedFileId);
        if (currentIndex > -1 && currentIndex < displayedFiles.length - 1) {
            const nextFile = displayedFiles[currentIndex + 1];
            setSelectedFileId(nextFile.id);
            setFiles(prev => prev.map(f => ({ ...f, isSelected: f.id === nextFile.id })));
            lastSelectedIdRef.current = nextFile.id;
        }
    }, [displayedFiles, selectedFileId]);
    
    const handlePrevTrack = useCallback(() => {
        const currentIndex = displayedFiles.findIndex(f => f.id === selectedFileId);
        if (currentIndex > 0) {
            const prevFile = displayedFiles[currentIndex - 1];
            setSelectedFileId(prevFile.id);
            setFiles(prev => prev.map(f => ({ ...f, isSelected: f.id === prevFile.id })));
             lastSelectedIdRef.current = prevFile.id;
        }
    }, [displayedFiles, selectedFileId]);
    
    const TableHeader = () => (
      <thead>
        <tr>
          <th className="w-12"><input type="checkbox" checked={allDisplayedFilesSelected} onChange={handleToggleSelectAll} disabled={isProcessing} className="h-4 w-4 rounded bg-slate-700 border-slate-600 text-accent-magenta focus:ring-accent-magenta"/></th>
          {(['originalName', 'bpm', 'key', 'time', 'dateAdded', 'state'] as const).map(key => (
            <th key={key} onClick={() => setSortConfig(prev => ({ key, direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc' }))}>
              { {originalName: 'Tytuł / Artysta', bpm: 'BPM', key: 'Tonacja', time: 'Czas', dateAdded: 'Data dodania', state: 'Status'}[key] }
              {sortConfig.key === key && <span className="sort-icon">{sortConfig.direction === 'asc' ? '▲' : '▼'}</span>}
            </th>
          ))}
          <th className="w-24">Akcje</th>
        </tr>
      </thead>
    );

    return (
        <div className="bg-bg-main min-h-screen font-sans text-text-light">
             <main className="container mx-auto px-4 py-8 flex flex-col" style={{height: '100vh'}}>
                {files.length === 0 ? (
                    <>
                        <WelcomeScreen onDirectoryConnect={handleDirectoryConnect}>
                             <FileDropzone onFilesSelected={handleFilesSelected} onUrlSubmitted={handleUrlSubmitted} isProcessing={isProcessing} />
                        </WelcomeScreen>
                    </>
                ) : (
                    <>
                        <HeaderToolbar
                           collectionName={activeViewDetails?.name}
                           totalCount={displayedFiles.length}
                           selectedCount={selectedFiles.length}
                           isAnalyzing={isBatchAnalyzing}
                           isSaving={isSaving}
                           onAnalyzeAll={() => handleBatchAnalyze(files.filter(f => f.state === ProcessingState.PENDING || f.state === ProcessingState.ERROR))}
                           onRename={() => setModalState({ type: 'rename' })}
                           onFindDuplicates={() => setModalState({ type: 'find-duplicates' })}
                           onXmlConvert={() => setModalState({ type: 'xml-converter' })}
                           isDirectAccessMode={!!directoryHandle}
                           directoryName={directoryHandle?.name}
                        />
                        <div className="grid grid-cols-1 lg:grid-cols-[250px_1fr_350px] gap-6 flex-grow min-h-0 mt-6">
                            <Sidebar
                                activeView={activeView}
                                onActiveViewChange={setActiveView}
                                smartCollections={smartCollections}
                                onNewCollection={() => setModalState({ type: 'smart-collection' })}
                                playlists={playlists}
                                onNewPlaylist={handleCreatePlaylist}
                                onRenamePlaylist={handleRenamePlaylist}
                                onDeletePlaylist={handleDeletePlaylist}
                                onAddTracksToPlaylist={handleAddTracksToPlaylist}
                                onIntelliSortPlaylist={handleIntelliSortPlaylist}
                                onExportPlaylist={handleExportPlaylist}
                            />

                            <main className="lg:col-start-2 flex flex-col gap-4 min-h-0">
                               <div className="table-container panel !p-0 flex-grow">
                                    {displayedFiles.length > 0 ? (
                                        <table className="track-table">
                                            <TableHeader />
                                            <tbody>
                                                {displayedFiles.map((file, index) => (
                                                    <FileListItem 
                                                        key={file.id} 
                                                        file={file} 
                                                        index={index}
                                                        isSelected={selectedFileId === file.id}
                                                        onSelect={(f, e) => handleSelect(f, e)}
                                                        onContextMenu={(f, e) => { e.preventDefault(); setContextMenu({ x: e.clientX, y: e.clientY, file: f}); }}
                                                        onSelectionChange={handleSelectionChange}
                                                        isPlaylistView={activeView.type === 'playlist'}
                                                        onReorder={(oldIndex, newIndex) => activeView.id && handleReorderPlaylist(activeView.id, oldIndex, newIndex)}
                                                    />
                                                ))}
                                            </tbody>
                                        </table>
                                    ) : (
                                        <EmptyState viewType={activeView.type} />
                                    )}
                                </div>
                            </main>

                            <TrackInfoPanel selectedFile={selectedFile} onSetHotcue={handleSetHotcue} onNext={handleNextTrack} onPrev={handlePrevTrack} />
                        </div>
                    </>
                )}
                {files.length > 0 && <Footer />}
            </main>
            
            {selectedFiles.length > 0 && <BatchActionsToolbar selectedCount={selectedFiles.length} isBatchProcessing={isBatchAnalyzing || isSaving} onClearSelection={handleClearSelection} onProcess={() => selectedFiles.forEach(handleProcessFile)} onDownload={() => handleDownloadOrSave(selectedFiles)} onBatchEdit={() => setModalState({type: 'batch-edit'})} onDelete={() => setModalState({ type: 'delete', fileId: 'selected' })} onBatchAnalyze={() => handleBatchAnalyze(selectedFiles)} />}

            {contextMenu && <TrackContextMenu menu={contextMenu} onClose={() => setContextMenu(null)} onAction={(action) => {
                const file = contextMenu.file;
                if (action.type === 'analyze') handleProcessFile(file);
                if (action.type === 'edit') setModalState({ type: 'edit', fileId: file.id });
                if (action.type === 'delete') setModalState({ type: 'delete', fileId: file.id });
                if (action.type === 'add-to-playlist') handleAddTracksToPlaylist(action.payload, [file.id]);
                if (action.type === 'remove-from-playlist' && activeView.type === 'playlist' && activeView.id) handleRemoveTrackFromPlaylist(activeView.id, file.id);
            }} playlists={playlists} isPlaylistView={activeView.type === 'playlist'} />}

            {modalState.type === 'edit' && modalFile && <EditTagsModal isOpen={true} file={modalFile} onClose={() => setModalState({ type: 'none' })} onSave={(tags) => handleSaveTags(modalFile.id, tags)} onApply={(tags) => handleApplyTags(modalFile.id, tags)} onManualSearch={(q, f) => handleProcessFile(f)} onZoomCover={(imageUrl) => setModalState({ type: 'zoom-cover', imageUrl })} isApplying={savingFileId === modalFile.id} isDirectAccessMode={!!directoryHandle} />}
            {modalState.type === 'settings' && <SettingsModal isOpen={true} onClose={() => setModalState({type: 'none'})} onSave={(keys, provider) => { setApiKeys(keys); setAiProvider(provider); setModalState({type: 'none'}); }} currentKeys={apiKeys} currentProvider={aiProvider} />}
            {modalState.type === 'rename' && <RenameModal isOpen={true} onClose={() => setModalState({type: 'none'})} onSave={handleSaveRename} currentPattern={renamePattern} files={selectedFiles} />}
            {modalState.type === 'batch-edit' && <BatchEditModal isOpen={true} onClose={() => setModalState({type: 'none'})} onSave={handleSaveBatchEdit} files={selectedFiles} />}
            {modalState.type === 'post-download' && <PostDownloadModal isOpen={true} count={modalState.count} onRemove={() => { handleDeleteFiles(selectedFiles.map(f => f.id)); setModalState({type: 'none'}); }} onKeep={() => setModalState({type: 'none'})} />}
            {modalState.type === 'zoom-cover' && <AlbumCoverModal isOpen={true} onClose={() => setModalState({type: 'none'})} imageUrl={modalState.imageUrl} />}
            {modalState.type === 'preview-changes' && <PreviewChangesModal isOpen={true} onCancel={() => setModalState({type: 'none'})} onConfirm={modalState.onConfirm} title={modalState.title} previews={modalState.previews}>{modalState.confirmationText}</PreviewChangesModal>}
            {modalState.type === 'delete' && <ConfirmationModal isOpen={true} onCancel={() => setModalState({type: 'none'})} onConfirm={() => {
                if (modalState.fileId === 'selected') handleDeleteFiles(selectedFiles.map(f => f.id));
                else if (modalState.fileId === 'all') handleClearAndReset();
                else handleDeleteFiles([modalState.fileId]);
                setModalState({type: 'none'});
            }} title="Potwierdź usunięcie">
                {modalState.fileId === 'selected' ? `Czy na pewno chcesz usunąć ${selectedFiles.length} zaznaczone pliki?` : modalState.fileId === 'all' ? 'Czy na pewno chcesz wyczyścić całą kolejkę?' : 'Czy na pewno chcesz usunąć ten plik?'} Ta operacja usunie pliki tylko z aplikacji.
            </ConfirmationModal>}
            {modalState.type === 'find-duplicates' && <DuplicateFinderModal isOpen={true} onClose={() => setModalState({type: 'none'})} files={files} onDelete={handleDeleteFiles} />}
            {modalState.type === 'xml-converter' && <XmlConverterModal isOpen={true} onClose={() => setModalState({type: 'none'})} />}
            {modalState.type === 'smart-collection' && <SmartCollectionModal isOpen={true} onClose={() => setModalState({type: 'none'})} onSave={handleSaveSmartCollection} files={files} />}

        </div>
    );
};

export default App;