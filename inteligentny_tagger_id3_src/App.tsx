

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';

// Layout components
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import PlayerBar from './components/PlayerBar';

// View components
import DashboardView from './components/DashboardView';
import LibraryView from './components/LibraryView';
import ImportView from './components/ImportView';
import DuplicatesView from './components/DuplicatesView';
import SettingsView from './components/SettingsView';
import PlayerView from './components/PlayerView';
import AiTaggerView from './components/AiTaggerView';
import XmlConverterView from './components/XmlConverterView';

// Modal components (preserved)
import EditTagsModal from './components/EditTagsModal';
import RenameModal from './components/RenameModal';
import ConfirmationModal from './components/ConfirmationModal';
import BatchEditModal from './components/BatchEditModal';
import PostDownloadModal from './components/PostDownloadModal';
import AlbumCoverModal from './components/AlbumCoverModal';
import PreviewChangesModal from './components/PreviewChangesModal';

// Types
import { AudioFile, ProcessingState, ID3Tags, ViewType, ActivityEntry } from './types';
import { AIProvider, ApiKeys, fetchTagsForFile, fetchTagsForBatch } from './services/aiService';

// Utils
import { readID3Tags, applyTags, saveFileDirectly, isTagWritingSupported, readAudioDuration } from './utils/audioUtils';
import { generatePath } from './utils/filenameUtils';
import { sortFiles, SortKey } from './utils/sortingUtils';
import { exportFilesToCsv } from './utils/csvUtils';

declare const uuid: { v4: () => string; };
declare const JSZip: any;
declare const saveAs: any;

const MAX_CONCURRENT_REQUESTS = 3;
const SUPPORTED_FORMATS = ['audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/flac', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/x-m4a', 'audio/aac', 'audio/x-ms-wma'];

interface RenamePreview {
    originalName: string;
    newName: string;
    isTooLong: boolean;
}

type ModalState =
  | { type: 'none' }
  | { type: 'edit'; fileId: string }
  | { type: 'rename' }
  | { type: 'delete'; fileId: string | 'selected' | 'all' }
  | { type: 'batch-edit' }
  | { type: 'post-download'; count: number }
  | { type: 'zoom-cover', imageUrl: string }
  | { type: 'preview-changes'; title: string; confirmationText: string; previews: RenamePreview[]; onConfirm: () => void; };

interface SerializableAudioFile {
  id: string; state: ProcessingState; originalTags: ID3Tags; fetchedTags?: ID3Tags;
  newName?: string; isSelected?: boolean; errorMessage?: string; dateAdded: number;
  webkitRelativePath?: string; fileName: string; fileType: string;
  duration?: number; rating?: number;
}

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

const App: React.FC = () => {
    const isRestoredRef = useRef(false);
    const [isRestored, setIsRestored] = useState(false);

    const [files, setFiles] = useState<AudioFile[]>(() => {
        const saved = localStorage.getItem('audioFiles');
        if (saved) {
            try {
                const parsed: SerializableAudioFile[] = JSON.parse(saved);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    isRestoredRef.current = true;
                    return parsed.map(f => ({ ...f, file: new File([], f.fileName, { type: f.fileType }), handle: null }));
                }
            } catch (e) { localStorage.removeItem('audioFiles'); }
        }
        return [];
    });

    const [isBatchAnalyzing, setIsBatchAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [savingFileId, setSavingFileId] = useState<string | null>(null);
    const [directoryHandle, setDirectoryHandle] = useState<any | null>(null);
    const [apiKeys, setApiKeys] = useState<ApiKeys>(() => JSON.parse(localStorage.getItem('apiKeys') || '{"grok":"","openai":""}'));
    const [aiProvider, setAiProvider] = useState<AIProvider>(() => (localStorage.getItem('aiProvider') as AIProvider) || 'gemini');
    const [sortKey, setSortKey] = useState<SortKey>(() => (localStorage.getItem('sortKey') as SortKey) || 'dateAdded');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(() => (localStorage.getItem('sortDirection') as 'asc' | 'desc') || 'asc');
    const [renamePattern, setRenamePattern] = useState<string>(() => localStorage.getItem('renamePattern') || '[artist] - [title]');
    const [modalState, setModalState] = useState<ModalState>({ type: 'none' });
    const [activeView, setActiveView] = useState<ViewType>('dashboard');
    const [globalSearch, setGlobalSearch] = useState('');
    const [playerCurrentFileId, setPlayerCurrentFileId] = useState<string | null>(null);
    const [activityLog, setActivityLog] = useState<ActivityEntry[]>(() => {
        try { return JSON.parse(localStorage.getItem('activityLog') || '[]'); } catch { return []; }
    });

    const processingQueueRef = useRef<string[]>([]);
    const activeRequestsRef = useRef(0);

    // Activity log helper
    const addActivityEntry = useCallback((entry: Omit<ActivityEntry, 'id' | 'timestamp'>) => {
        const newEntry: ActivityEntry = { ...entry, id: uuid?.v4?.() || Math.random().toString(36), timestamp: Date.now() };
        setActivityLog(prev => [newEntry, ...prev].slice(0, 20));
    }, []);

    useEffect(() => {
        if (isRestoredRef.current) {
            setIsRestored(true);
            isRestoredRef.current = false;
            setActiveView('library');
        } else if (files.length === 0) {
            setActiveView('import');
        }
    }, []);

    useEffect(() => { localStorage.setItem('apiKeys', JSON.stringify(apiKeys)); }, [apiKeys]);
    useEffect(() => { localStorage.setItem('aiProvider', aiProvider); }, [aiProvider]);
    useEffect(() => { localStorage.setItem('sortKey', sortKey); }, [sortKey]);
    useEffect(() => { localStorage.setItem('sortDirection', sortDirection); }, [sortDirection]);
    useEffect(() => { localStorage.setItem('renamePattern', renamePattern); }, [renamePattern]);
    useEffect(() => { localStorage.setItem('activityLog', JSON.stringify(activityLog)); }, [activityLog]);

    useEffect(() => {
        if (files.length === 0 && !isRestored) {
            localStorage.removeItem('audioFiles');
            return;
        }
        const serializableFiles: SerializableAudioFile[] = files.map(f => ({
            id: f.id, state: f.state, originalTags: f.originalTags, fetchedTags: f.fetchedTags,
            newName: f.newName, isSelected: f.isSelected, errorMessage: f.errorMessage, dateAdded: f.dateAdded,
            webkitRelativePath: f.webkitRelativePath, fileName: f.file.name, fileType: f.file.type,
            duration: f.duration, rating: f.rating,
        }));
        localStorage.setItem('audioFiles', JSON.stringify(serializableFiles));
    }, [files, isRestored]);

    useEffect(() => {
        setFiles(currentFiles => currentFiles.map(file => ({ ...file, newName: generatePath(renamePattern, file.fetchedTags || file.originalTags, file.file.name) })));
    }, [renamePattern, files.map(f => f.fetchedTags).join(',')]);

    const updateFileState = useCallback((id: string, updates: Partial<AudioFile>) => {
        setFiles(prevFiles => prevFiles.map(f => f.id === id ? { ...f, ...updates } : f));
    }, []);

    const processQueue = useCallback(async () => {
        if (activeRequestsRef.current >= MAX_CONCURRENT_REQUESTS || processingQueueRef.current.length === 0) return;
        const fileId = processingQueueRef.current.shift();
        if (!fileId) return;
        const file = files.find(f => f.id === fileId);
        if (!file || file.state !== ProcessingState.PENDING) { processQueue(); return; }
        activeRequestsRef.current++;
        updateFileState(fileId, { state: ProcessingState.PROCESSING });
        try {
            const fetchedTags = await fetchTagsForFile(file.file.name, file.originalTags, aiProvider, apiKeys);
            updateFileState(fileId, { state: ProcessingState.SUCCESS, fetchedTags });
            addActivityEntry({ type: 'ai_tag', message: `Otagowano: ${file.originalTags.title || file.file.name}` });
        } catch (error) {
            updateFileState(fileId, { state: ProcessingState.ERROR, errorMessage: error instanceof Error ? error.message : "Błąd" });
        } finally {
            activeRequestsRef.current--;
            processQueue();
        }
    }, [files, aiProvider, apiKeys, updateFileState, addActivityEntry]);

    const handleClearAndReset = () => { setFiles([]); setIsRestored(false); setDirectoryHandle(null); setActiveView('import'); };

    const addFilesToQueue = useCallback(async (filesToAdd: { file: File, handle?: any, path?: string }[]) => {
        if (typeof uuid === 'undefined') { alert("Błąd: Biblioteka 'uuid' nie załadowana."); return; }
        const validAudioFiles = filesToAdd.filter(item => SUPPORTED_FORMATS.includes(item.file.type));
        if (validAudioFiles.length === 0) throw new Error(`Brak obsługiwanych formatów audio.`);
        setIsRestored(false);
        const newAudioFiles: AudioFile[] = await Promise.all(validAudioFiles.map(async item => {
            const tags = await readID3Tags(item.file);
            const duration = await readAudioDuration(item.file);
            return {
                id: uuid.v4(), file: item.file, handle: item.handle,
                webkitRelativePath: item.path || item.file.webkitRelativePath,
                state: ProcessingState.PENDING, originalTags: tags, dateAdded: Date.now(), duration,
            };
        }));
        setFiles(prev => [...prev, ...newAudioFiles]);
        addActivityEntry({ type: 'import', message: `Zaimportowano ${newAudioFiles.length} plików`, fileCount: newAudioFiles.length });
        setActiveView('library');
        if (!directoryHandle) {
            processingQueueRef.current.push(...newAudioFiles.map(f => f.id));
            for(let i=0; i<MAX_CONCURRENT_REQUESTS; i++) processQueue();
        }
    }, [processQueue, directoryHandle, addActivityEntry]);

    const handleFilesSelected = useCallback(async (selectedFiles: FileList) => {
        try { await addFilesToQueue(Array.from(selectedFiles).map(f => ({ file: f }))); }
        catch (e) { alert(`Błąd: ${e instanceof Error ? e.message : e}`); }
    }, [addFilesToQueue]);

    const handleDirectoryConnect = useCallback(async (handle: any) => {
        setIsRestored(false); setDirectoryHandle(handle); setFiles([]);
        try {
            const filesToProcess: { file: File, handle: any, path: string }[] = [];
            for await (const fileData of getFilesRecursively(handle)) filesToProcess.push(fileData);
            await addFilesToQueue(filesToProcess);
        } catch (e) { alert(`Błąd: ${e instanceof Error ? e.message : e}`); setDirectoryHandle(null); }
    }, [addFilesToQueue]);

    const handleUrlSubmitted = async (url: string) => {
        if (!url) return;
        try {
            const response = await fetch('https://api.allorigins.win/raw?url=' + encodeURIComponent(url));
            if (!response.ok) throw new Error(`Błąd pobierania: ${response.statusText}`);
            const blob = await response.blob();
            if (!SUPPORTED_FORMATS.some(f => blob.type.startsWith(f.split('/')[0]))) throw new Error(`Nieobsługiwany typ: ${blob.type}`);
            let filename = 'remote_file.mp3'; try { filename = decodeURIComponent(new URL(url).pathname.split('/').pop() || filename); } catch {}
            await addFilesToQueue([{ file: new File([blob], filename, { type: blob.type }) }]);
        } catch (e) { alert(`Błąd URL: ${e instanceof Error ? e.message : e}`); throw e; }
    };

    const handleProcessFile = useCallback((file: AudioFile) => {
        if (!processingQueueRef.current.includes(file.id)) processingQueueRef.current.push(file.id);
        processQueue();
    }, [processQueue]);

    const sortedFiles = useMemo(() => sortFiles([...files], sortKey, sortDirection), [files, sortKey, sortDirection]);
    const selectedFiles = useMemo(() => files.filter(f => f.isSelected), [files]);
    const allFilesSelected = useMemo(() => files.length > 0 && files.every(f => f.isSelected), [files]);
    const isProcessing = useMemo(() => files.some(f => f.state === ProcessingState.PROCESSING), [files]);
    const modalFile = useMemo(() => (modalState.type === 'edit') ? files.find(f => f.id === modalState.fileId) : undefined, [modalState, files]);

    const handleSelectionChange = (fileId: string, isSelected: boolean) => updateFileState(fileId, { isSelected });
    const handleToggleSelectAll = () => setFiles(prev => prev.map(f => ({ ...f, isSelected: !allFilesSelected })));
    const handleSaveSettings = (keys: ApiKeys, provider: AIProvider) => { setApiKeys(keys); setAiProvider(provider); };

    const handleDelete = (fileId: string) => {
        if (fileId === 'all') handleClearAndReset();
        else if (fileId === 'selected') setFiles(f => f.filter(file => !file.isSelected));
        else setFiles(f => f.filter(file => file.id !== fileId));
        setModalState({ type: 'none' });
    };

    const openDeleteModal = (id: string | 'selected' | 'all') => {
        if (id === 'selected' && selectedFiles.length === 0) { alert("Nie wybrano plików."); return; }
        setModalState({ type: 'delete', fileId: id });
    };

    const handleSaveTags = (fileId: string, tags: ID3Tags) => {
        updateFileState(fileId, { fetchedTags: tags });
        setModalState({ type: 'none' });
        addActivityEntry({ type: 'tags_edited', message: `Edytowano tagi: ${tags.title || fileId}` });
    };

    const handleApplyTags = async (fileId: string, tags: ID3Tags) => {
        if (!directoryHandle) return;
        const file = files.find(f => f.id === fileId);
        if (!file || !file.handle) return;
        setSavingFileId(fileId);
        try {
            const result = await saveFileDirectly(directoryHandle, { ...file, fetchedTags: tags });
            if (result.success && result.updatedFile) {
                updateFileState(fileId, { ...result.updatedFile, state: ProcessingState.SUCCESS });
                setModalState({ type: 'none' });
            } else updateFileState(fileId, { state: ProcessingState.ERROR, errorMessage: result.errorMessage, fetchedTags: tags });
        } catch (e) { updateFileState(fileId, { state: ProcessingState.ERROR, errorMessage: e instanceof Error ? e.message : "Błąd", fetchedTags: tags });
        } finally { setSavingFileId(null); }
    };

    const handleManualSearch = async (query: string, file: AudioFile) => {
        updateFileState(file.id, { state: ProcessingState.PROCESSING });
        try {
            const fetchedTags = await fetchTagsForFile(query, file.originalTags, aiProvider, apiKeys);
            updateFileState(file.id, { state: ProcessingState.SUCCESS, fetchedTags });
        } catch (e) { updateFileState(file.id, { state: ProcessingState.ERROR, errorMessage: e instanceof Error ? e.message : "Błąd" }); throw e; }
    };

    const handleSaveRenamePattern = (newPattern: string) => {
        const filesToPreview = selectedFiles.length > 0 ? selectedFiles : files.slice(0, 5);
        if (filesToPreview.length === 0) { setRenamePattern(newPattern); return; }
        const previews = filesToPreview.map(f => ({ originalName: f.webkitRelativePath || f.file.name, newName: generatePath(newPattern, f.fetchedTags || f.originalTags, f.file.name), isTooLong: (f.newName || "").length > 255 }));
        setModalState({ type: 'preview-changes', title: 'Potwierdź zmianę szablonu', confirmationText: 'Nowy szablon zostanie zastosowany. Czy kontynuować?', previews, onConfirm: () => { setRenamePattern(newPattern); setModalState({ type: 'none' }); } });
    };

    const handleBatchEditSave = (tagsToApply: Partial<ID3Tags>) => {
        setFiles(f => f.map(file => {
            if (file.isSelected) {
                const newTags = { ...file.fetchedTags, ...tagsToApply };
                Object.keys(tagsToApply).forEach(k => { if (tagsToApply[k as keyof ID3Tags] === '') delete newTags[k as keyof ID3Tags]; });
                return { ...file, fetchedTags: newTags };
            } return file;
        }));
        setModalState({ type: 'none' });
        addActivityEntry({ type: 'tags_edited', message: `Edycja hurtowa: ${selectedFiles.length} plików` });
    };

    const executeDownloadOrSave = async () => {
        setIsSaving(true);
        if (directoryHandle) {
            const filesToSave = selectedFiles.filter(f => f.handle);
            const fileIdsToSave = filesToSave.map(f => f.id);
            setFiles(files => files.map(f => fileIdsToSave.includes(f.id) ? { ...f, state: ProcessingState.DOWNLOADING } : f));
            const results = await Promise.all(filesToSave.map(file => saveFileDirectly(directoryHandle, file)));
            let successCount = 0;
            const updates = new Map<string, Partial<AudioFile>>();
            results.forEach((result, index) => {
                const originalFile = filesToSave[index];
                if (result.success && result.updatedFile) {
                    successCount++;
                    updates.set(originalFile.id, { ...result.updatedFile, state: ProcessingState.SUCCESS, isSelected: false });
                } else {
                    updates.set(originalFile.id, { state: ProcessingState.ERROR, errorMessage: result.errorMessage });
                }
            });
            setFiles(currentFiles => currentFiles.map(file => updates.has(file.id) ? { ...file, ...updates.get(file.id) } : file));
            addActivityEntry({ type: 'export', message: `Zapisano ${successCount} plików na dysk` });
            alert(`Zapisano pomyślnie ${successCount} z ${filesToSave.length} plików.`);
        } else {
            const filesToDownload = selectedFiles.filter(f => f.state === ProcessingState.SUCCESS || f.state === ProcessingState.PENDING);
            const downloadableFileIds = filesToDownload.map(f => f.id);
            setFiles(files => files.map(f => downloadableFileIds.includes(f.id) ? { ...f, state: ProcessingState.DOWNLOADING } : f));
            const zip = new JSZip();
            const errorUpdates = new Map<string, Partial<AudioFile>>();
            await Promise.all(filesToDownload.map(async (audioFile) => {
                const finalName = generatePath(renamePattern, audioFile.fetchedTags || audioFile.originalTags, audioFile.file.name) || audioFile.file.name;
                try {
                    if (isTagWritingSupported(audioFile.file) && audioFile.fetchedTags) {
                         const blob = await applyTags(audioFile.file, audioFile.fetchedTags);
                         zip.file(finalName, blob);
                    } else {
                        zip.file(finalName, audioFile.file);
                    }
                } catch (error) {
                    errorUpdates.set(audioFile.id, { state: ProcessingState.ERROR, errorMessage: error instanceof Error ? error.message : "Błąd zapisu tagów." });
                }
            }));
            if (Object.keys(zip.files).length > 0) {
                const zipBlob = await zip.generateAsync({ type: 'blob' });
                saveAs(zipBlob, 'tagged-music.zip');
                setModalState({ type: 'post-download', count: Object.keys(zip.files).length });
                addActivityEntry({ type: 'export', message: `Pobrano ZIP: ${Object.keys(zip.files).length} plików` });
            }
            setFiles(files => files.map(f => {
                if (errorUpdates.has(f.id)) return { ...f, ...errorUpdates.get(f.id) };
                if (downloadableFileIds.includes(f.id) && f.state === ProcessingState.DOWNLOADING) return { ...f, state: ProcessingState.SUCCESS };
                return f;
            }));
        }
        setIsSaving(false);
    };

    const handleDownloadOrSave = async () => {
        const filesToProcess = selectedFiles.length > 0 ? selectedFiles : [];
        if (filesToProcess.length === 0) {
            alert("Nie wybrano żadnych plików do zapisania lub pobrania.");
            return;
        }
        const previews = filesToProcess.map(file => ({
            originalName: file.webkitRelativePath || file.file.name,
            newName: file.newName || file.file.name,
            isTooLong: (file.newName || file.file.name).length > 255
        })).filter(p => p.originalName !== p.newName);

        if (previews.length === 0) {
            await executeDownloadOrSave();
            return;
        }
        setModalState({
            type: 'preview-changes',
            title: `Potwierdź ${directoryHandle ? 'zapis i zmianę nazw' : 'pobieranie ze zmianą nazw'}`,
            confirmationText: `Nazwy ${previews.length} z ${selectedFiles.length} zaznaczonych plików zostaną zmienione. Czy kontynuować?`,
            previews: previews,
            onConfirm: () => { setModalState({ type: 'none' }); setTimeout(() => executeDownloadOrSave(), 50); }
        });
    };

    const handleExportCsv = () => {
        if (files.length === 0) return alert("Brak plików do wyeksportowania.");
        try {
            const csvData = exportFilesToCsv(files);
            const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
            saveAs(blob, `id3-tagger-export-${new Date().toISOString().replace(/[:.]/g, '-')}.csv`);
            addActivityEntry({ type: 'export', message: `Eksport CSV: ${files.length} plików` });
        } catch (error) {
            alert(`Błąd eksportu CSV: ${error instanceof Error ? error.message : String(error)}`);
        }
    };

    const handlePostDownloadRemove = () => { setFiles(f => f.filter(file => !file.isSelected)); setModalState({ type: 'none' }); };

    const handleBatchAnalyze = async (filesToProcess: AudioFile[]) => {
        if (filesToProcess.length === 0 || isBatchAnalyzing) return;
        const ids = filesToProcess.map(f => f.id);
        setIsBatchAnalyzing(true);
        setFiles(prev => prev.map(f => ids.includes(f.id) ? { ...f, state: ProcessingState.PROCESSING } : f));
        try {
            const results = await fetchTagsForBatch(filesToProcess, aiProvider, apiKeys);
            const resultsMap = new Map(results.map(r => [r.originalFilename, r]));
            setFiles(prev => prev.map(f => {
                if (ids.includes(f.id)) {
                    const result = resultsMap.get(f.file.name);
                    if (result) {
                        const { originalFilename, ...tags } = result;
                        return { ...f, state: ProcessingState.SUCCESS, fetchedTags: { ...f.originalTags, ...tags } };
                    } return { ...f, state: ProcessingState.ERROR, errorMessage: "Brak odpowiedzi AI." };
                } return f;
            }));
            addActivityEntry({ type: 'ai_tag', message: `Batch AI: otagowano ${ids.length} plików`, fileCount: ids.length });
        } catch (e) {
            setFiles(prev => prev.map(f => ids.includes(f.id) ? { ...f, state: ProcessingState.ERROR, errorMessage: e instanceof Error ? e.message : "Błąd" } : f));
        } finally { setIsBatchAnalyzing(false); }
    };

    const handleBatchAnalyzeAll = () => {
        const toAnalyze = files.filter(f => f.state !== ProcessingState.SUCCESS);
        if (toAnalyze.length === 0) return alert("Wszystkie pliki przetworzone.");
        handleBatchAnalyze(toAnalyze);
    };

    const handleRatingChange = useCallback((fileId: string, rating: number) => {
        updateFileState(fileId, { rating });
    }, [updateFileState]);

    const handleDeleteFiles = useCallback((fileIds: string[]) => {
        setFiles(prev => prev.filter(f => !fileIds.includes(f.id)));
    }, []);

    const handleDirectoryPicker = async () => {
        try {
            if (!('showDirectoryPicker' in window)) {
                alert("Twoja przeglądarka nie obsługuje File System Access API.");
                return;
            }
            const handle = await (window as any).showDirectoryPicker();
            handleDirectoryConnect(handle);
        } catch (e) {
            if (e instanceof Error && e.name !== 'AbortError') {
                alert(`Błąd: ${e.message}`);
            }
        }
    };

    const filesForRenamePreview = selectedFiles.length > 0 ? selectedFiles : files.slice(0, 5);
    const playerFile = useMemo(() => files.find(f => f.id === playerCurrentFileId) || null, [files, playerCurrentFileId]);

    return (
        <div style={{ display: 'flex', height: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>
            <Sidebar activeView={activeView} onNavigate={setActiveView} fileCount={files.length} />

            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <TopBar
                    searchQuery={globalSearch}
                    onSearchChange={setGlobalSearch}
                    activeView={activeView}
                />

                <main style={{ flex: 1, overflowY: 'auto', padding: '24px', paddingBottom: '100px' }}>
                    {activeView === 'dashboard' && (
                        <DashboardView
                            activityLog={activityLog}
                            fileCount={files.length}
                            onNavigate={setActiveView}
                        />
                    )}
                    {activeView === 'library' && (
                        <LibraryView
                            files={sortedFiles}
                            sortKey={sortKey}
                            sortDirection={sortDirection}
                            onSortChange={(key, dir) => { setSortKey(key); setSortDirection(dir); }}
                            globalSearch={globalSearch}
                            onEditFile={(id) => setModalState({ type: 'edit', fileId: id })}
                            onDeleteFile={(id) => openDeleteModal(id)}
                            onProcessFile={handleProcessFile}
                            onSelectionChange={handleSelectionChange}
                            onToggleSelectAll={handleToggleSelectAll}
                            allFilesSelected={allFilesSelected}
                            selectedFiles={selectedFiles}
                            onBatchAnalyze={handleBatchAnalyze}
                            onBatchAnalyzeAll={handleBatchAnalyzeAll}
                            onDownloadOrSave={handleDownloadOrSave}
                            onBatchEdit={() => setModalState({ type: 'batch-edit' })}
                            onExportCsv={handleExportCsv}
                            onDeleteSelected={() => openDeleteModal('selected')}
                            onClearAll={() => openDeleteModal('all')}
                            onRenamePattern={() => setModalState({ type: 'rename' })}
                            isBatchAnalyzing={isBatchAnalyzing}
                            isSaving={isSaving}
                            directoryHandle={directoryHandle}
                            isRestored={isRestored}
                            onSetPlayer={setPlayerCurrentFileId}
                            onRatingChange={handleRatingChange}
                        />
                    )}
                    {activeView === 'import' && (
                        <ImportView
                            onFilesSelected={handleFilesSelected}
                            onDirectoryConnect={handleDirectoryConnect}
                            onDirectoryPicker={handleDirectoryPicker}
                            onUrlSubmitted={handleUrlSubmitted}
                            isProcessing={isProcessing}
                            onNavigate={setActiveView}
                        />
                    )}
                    {activeView === 'duplicates' && (
                        <DuplicatesView
                            files={files}
                            onDeleteFiles={handleDeleteFiles}
                            onUpdateFiles={(updates) => setFiles(prev => prev.map(f => {
                                const u = updates.find(u => u.id === f.id);
                                return u ? { ...f, ...u } : f;
                            }))}
                        />
                    )}
                    {activeView === 'settings' && (
                        <SettingsView
                            apiKeys={apiKeys}
                            aiProvider={aiProvider}
                            renamePattern={renamePattern}
                            onSave={handleSaveSettings}
                            onRenamePatternChange={setRenamePattern}
                        />
                    )}
                    {activeView === 'player' && (
                        <PlayerView
                            files={sortedFiles}
                            currentFileId={playerCurrentFileId}
                            onFileChange={setPlayerCurrentFileId}
                        />
                    )}
                    {activeView === 'tagger' && (
                        <AiTaggerView
                            files={files}
                            aiProvider={aiProvider}
                            apiKeys={apiKeys}
                            isBatchAnalyzing={isBatchAnalyzing}
                            onAiProvider={setAiProvider}
                            onProcessFile={handleProcessFile}
                            onBatchAnalyze={handleBatchAnalyze}
                            onBatchAnalyzeAll={handleBatchAnalyzeAll}
                            onEditFile={(id) => setModalState({ type: 'edit', fileId: id })}
                            onSelectionChange={handleSelectionChange}
                        />
                    )}
                    {activeView === 'converter' && (
                        <XmlConverterView files={files} />
                    )}
                </main>

                <PlayerBar
                    currentFile={playerFile}
                    files={sortedFiles}
                    onFileChange={setPlayerCurrentFileId}
                    onNavigateToPlayer={() => setActiveView('player')}
                />
            </div>

            {/* Modalne dialogi */}
            {modalState.type === 'edit' && modalFile && (
                <EditTagsModal
                    isOpen={true}
                    onClose={() => setModalState({ type: 'none' })}
                    onSave={(tags) => handleSaveTags(modalFile.id, tags)}
                    onApply={(tags) => handleApplyTags(modalFile.id, tags)}
                    isApplying={savingFileId === modalFile.id}
                    isDirectAccessMode={!!directoryHandle}
                    file={modalFile}
                    onManualSearch={handleManualSearch}
                    onZoomCover={(imageUrl) => setModalState({ type: 'zoom-cover', imageUrl })}
                />
            )}
            {modalState.type === 'rename' && (
                <RenameModal
                    isOpen={true}
                    onClose={() => setModalState({ type: 'none' })}
                    onSave={handleSaveRenamePattern}
                    currentPattern={renamePattern}
                    files={filesForRenamePreview}
                />
            )}
            {modalState.type === 'delete' && (
                <ConfirmationModal
                    isOpen={true}
                    onCancel={() => setModalState({ type: 'none' })}
                    onConfirm={() => handleDelete(modalState.fileId)}
                    title="Potwierdź usunięcie"
                >
                    {`Czy na pewno chcesz usunąć ${modalState.fileId === 'all' ? 'wszystkie pliki' : modalState.fileId === 'selected' ? `${selectedFiles.length} zaznaczone pliki` : 'ten plik'} z kolejki?`}
                </ConfirmationModal>
            )}
            {modalState.type === 'batch-edit' && (
                <BatchEditModal
                    isOpen={true}
                    onClose={() => setModalState({ type: 'none' })}
                    onSave={handleBatchEditSave}
                    files={selectedFiles}
                />
            )}
            {modalState.type === 'post-download' && (
                <PostDownloadModal
                    isOpen={true}
                    onKeep={() => setModalState({ type: 'none' })}
                    onRemove={handlePostDownloadRemove}
                    count={modalState.count}
                />
            )}
            {modalState.type === 'zoom-cover' && (
                <AlbumCoverModal
                    isOpen={true}
                    onClose={() => setModalState({ type: 'none' })}
                    imageUrl={modalState.imageUrl}
                />
            )}
            {modalState.type === 'preview-changes' && (
                <PreviewChangesModal
                    isOpen={true}
                    onCancel={() => setModalState({ type: 'none' })}
                    onConfirm={modalState.onConfirm}
                    title={modalState.title}
                    previews={modalState.previews}
                >
                    {modalState.confirmationText}
                </PreviewChangesModal>
            )}
        </div>
    );
};

export default App;
