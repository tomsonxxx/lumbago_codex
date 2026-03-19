

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';

// Components
import Footer from './components/Footer';
import ThemeToggle from './components/ThemeToggle';
import SettingsModal from './components/SettingsModal';
import EditTagsModal from './components/EditTagsModal';
import RenameModal from './components/RenameModal';
import ConfirmationModal from './components/ConfirmationModal';
import BatchEditModal from './components/BatchEditModal';
import PostDownloadModal from './components/PostDownloadModal';
import AlbumCoverModal from './components/AlbumCoverModal';
import PreviewChangesModal from './components/PreviewChangesModal';
import MainToolbar from './components/MainToolbar';
import TabbedInterface, { Tab } from './components/TabbedInterface';
import LibraryTab from './components/LibraryTab';
import ScanTab from './components/ScanTab';
import PlaceholderTab from './components/PlaceholderTab';

// Types
import { AudioFile, ProcessingState, ID3Tags } from './types';
import { AIProvider, ApiKeys, fetchTagsForFile, fetchTagsForBatch } from './services/aiService';

// Utils
import { readID3Tags, applyTags, saveFileDirectly, isTagWritingSupported } from './utils/audioUtils';
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
  | { type: 'settings' }
  | { type: 'batch-edit' }
  | { type: 'post-download'; count: number }
  | { type: 'zoom-cover', imageUrl: string }
  | { type: 'preview-changes'; title: string; confirmationText: string; previews: RenamePreview[]; onConfirm: () => void; };

interface SerializableAudioFile {
  id: string; state: ProcessingState; originalTags: ID3Tags; fetchedTags?: ID3Tags;
  newName?: string; isSelected?: boolean; errorMessage?: string; dateAdded: number;
  webkitRelativePath?: string; fileName: string; fileType: string;
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
    const [theme, setTheme] = useState<'light' | 'dark'>(() => (localStorage.getItem('theme') as 'light' | 'dark') || 'dark');
    const [apiKeys, setApiKeys] = useState<ApiKeys>(() => JSON.parse(localStorage.getItem('apiKeys') || '{"grok":"","openai":""}'));
    const [aiProvider, setAiProvider] = useState<AIProvider>(() => (localStorage.getItem('aiProvider') as AIProvider) || 'gemini');
    const [sortKey, setSortKey] = useState<SortKey>(() => (localStorage.getItem('sortKey') as SortKey) || 'dateAdded');
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(() => (localStorage.getItem('sortDirection') as 'asc' | 'desc') || 'asc');
    const [renamePattern, setRenamePattern] = useState<string>(() => localStorage.getItem('renamePattern') || '[artist] - [title]');
    const [modalState, setModalState] = useState<ModalState>({ type: 'none' });
    const [activeTab, setActiveTab] = useState('library');

    const processingQueueRef = useRef<string[]>([]);
    const activeRequestsRef = useRef(0);

    useEffect(() => {
        if (isRestoredRef.current) {
            setIsRestored(true);
            isRestoredRef.current = false;
            setActiveTab('library');
        } else if (files.length === 0) {
            setActiveTab('scan');
        }
    }, []); // Only run once on mount
    
    useEffect(() => { localStorage.setItem('theme', theme); document.documentElement.className = theme; }, [theme]);
    useEffect(() => { localStorage.setItem('apiKeys', JSON.stringify(apiKeys)); }, [apiKeys]);
    useEffect(() => { localStorage.setItem('aiProvider', aiProvider); }, [aiProvider]);
    useEffect(() => { localStorage.setItem('sortKey', sortKey); }, [sortKey]);
    useEffect(() => { localStorage.setItem('sortDirection', sortDirection); }, [sortDirection]);
    useEffect(() => { localStorage.setItem('renamePattern', renamePattern); }, [renamePattern]);

    useEffect(() => {
        if (files.length === 0 && !isRestored) {
            localStorage.removeItem('audioFiles');
            return;
        }
        const serializableFiles: SerializableAudioFile[] = files.map(f => ({
            id: f.id, state: f.state, originalTags: f.originalTags, fetchedTags: f.fetchedTags,
            newName: f.newName, isSelected: f.isSelected, errorMessage: f.errorMessage, dateAdded: f.dateAdded,
            webkitRelativePath: f.webkitRelativePath, fileName: f.file.name, fileType: f.file.type,
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
        } catch (error) {
            updateFileState(fileId, { state: ProcessingState.ERROR, errorMessage: error instanceof Error ? error.message : "Błąd" });
        } finally {
            activeRequestsRef.current--;
            processQueue();
        }
    }, [files, aiProvider, apiKeys, updateFileState]);

    const handleClearAndReset = () => { setFiles([]); setIsRestored(false); setDirectoryHandle(null); setActiveTab('scan'); };

    const addFilesToQueue = useCallback(async (filesToAdd: { file: File, handle?: any, path?: string }[]) => {
        if (typeof uuid === 'undefined') { alert("Błąd: Biblioteka 'uuid' nie załadowana."); return; }
        const validAudioFiles = filesToAdd.filter(item => SUPPORTED_FORMATS.includes(item.file.type));
        if (validAudioFiles.length === 0) throw new Error(`Brak obsługiwanych formatów audio.`);
        setIsRestored(false);
        const newAudioFiles: AudioFile[] = await Promise.all(validAudioFiles.map(async item => ({
            id: uuid.v4(), file: item.file, handle: item.handle, webkitRelativePath: item.path || item.file.webkitRelativePath,
            state: ProcessingState.PENDING, originalTags: await readID3Tags(item.file), dateAdded: Date.now(),
        })));
        setFiles(prev => [...prev, ...newAudioFiles]);
        setActiveTab('library');
        if (!directoryHandle) {
            processingQueueRef.current.push(...newAudioFiles.map(f => f.id));
            for(let i=0; i<MAX_CONCURRENT_REQUESTS; i++) processQueue();
        }
    }, [processQueue, directoryHandle]);

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
    const handleSaveSettings = (keys: ApiKeys, provider: AIProvider) => { setApiKeys(keys); setAiProvider(provider); setModalState({ type: 'none' }); };
    
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

    const handleSaveTags = (fileId: string, tags: ID3Tags) => { updateFileState(fileId, { fetchedTags: tags }); setModalState({ type: 'none' }); };

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
        if (filesToPreview.length === 0) { setRenamePattern(newPattern); setModalState({ type: 'none' }); return; }
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
            confirmationText: `Nazwy ${previews.length} z ${selectedFiles.length} zaznaczonych plików zostaną zmienione zgodnie z szablonem przed zapisaniem. Czy chcesz kontynuować?`,
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
        } catch (error) {
            alert(`Wystąpił błąd podczas eksportowania pliku CSV: ${error instanceof Error ? error.message : String(error)}`);
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
        } catch (e) {
            setFiles(prev => prev.map(f => ids.includes(f.id) ? { ...f, state: ProcessingState.ERROR, errorMessage: e instanceof Error ? e.message : "Błąd" } : f));
        } finally { setIsBatchAnalyzing(false); }
    };
    
    const handleBatchAnalyzeAll = () => {
        const toAnalyze = files.filter(f => f.state !== ProcessingState.SUCCESS);
        if (toAnalyze.length === 0) return alert("Wszystkie pliki przetworzone.");
        handleBatchAnalyze(toAnalyze);
    };

    const handleDirectoryPicker = async () => {
        try {
            if (!('showDirectoryPicker' in window)) {
                alert("Twoja przeglądarka nie obsługuje File System Access API. Użyj zakładki 'Import / Skan' do ręcznego wyboru plików.");
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
    
    const tabs: Tab[] = [
        { id: 'library', label: 'Biblioteka', component: <LibraryTab 
            files={files} sortedFiles={sortedFiles} selectedFiles={selectedFiles} allFilesSelected={allFilesSelected}
            isBatchAnalyzing={isBatchAnalyzing} isSaving={isSaving} directoryHandle={directoryHandle} isRestored={isRestored}
            onToggleSelectAll={handleToggleSelectAll} onBatchAnalyze={handleBatchAnalyze} onBatchAnalyzeAll={handleBatchAnalyzeAll}
            onDownloadOrSave={handleDownloadOrSave} onBatchEdit={() => setModalState({ type: 'batch-edit' })}
            onSingleItemEdit={(id) => setModalState({ type: 'edit', fileId: id })} onRename={() => setModalState({ type: 'rename' })}
            onExportCsv={handleExportCsv} onDeleteItem={openDeleteModal} onClearAll={() => openDeleteModal('all')}
            onProcessFile={handleProcessFile} onSelectionChange={handleSelectionChange} onTabChange={setActiveTab}
        /> },
        { id: 'scan', label: 'Import / Skan', component: <ScanTab 
            onFilesSelected={handleFilesSelected} onUrlSubmitted={handleUrlSubmitted}
            onDirectoryConnect={handleDirectoryConnect} isProcessing={isProcessing}
        /> },
        { id: 'player', label: 'Odtwarzacz', component: <PlaceholderTab title="Odtwarzacz" /> },
        { id: 'tagger', label: 'Smart Tagger AI', component: <PlaceholderTab title="Smart Tagger AI" /> },
        { id: 'duplicates', label: 'Wyszukiwarka Duplikatów', component: <PlaceholderTab title="Wyszukiwarka Duplikatów" /> },
        { id: 'converter', label: 'Konwerter XML', component: <PlaceholderTab title="Konwerter XML" /> },
    ];

    return (
        <div className="bg-slate-50 dark:bg-slate-900 min-h-screen font-sans text-slate-800 dark:text-slate-200">
            <main className="container mx-auto px-4 py-8">
                <header className="flex justify-between items-center mb-4">
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Lumbago Music AI</h1>
                    <div className="flex items-center space-x-2">
                         <ThemeToggle theme={theme} setTheme={setTheme} />
                         <button onClick={() => setModalState({ type: 'settings' })} className="p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" title="Ustawienia">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                         </button>
                    </div>
                </header>
                
                <MainToolbar onTabChange={setActiveTab} onDirectorySelect={handleDirectoryPicker} />
                <TabbedInterface tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
                
                <Footer />
            </main>
            
            {modalState.type === 'settings' && <SettingsModal isOpen={true} onClose={() => setModalState({ type: 'none' })} onSave={handleSaveSettings} currentKeys={apiKeys} currentProvider={aiProvider} />}
            {modalState.type === 'edit' && modalFile && <EditTagsModal isOpen={true} onClose={() => setModalState({ type: 'none' })} onSave={(tags) => handleSaveTags(modalFile.id, tags)} onApply={(tags) => handleApplyTags(modalFile.id, tags)} isApplying={savingFileId === modalFile.id} isDirectAccessMode={!!directoryHandle} file={modalFile} onManualSearch={handleManualSearch} onZoomCover={(imageUrl) => setModalState({ type: 'zoom-cover', imageUrl })} />}
            {modalState.type === 'rename' && <RenameModal isOpen={true} onClose={() => setModalState({ type: 'none' })} onSave={handleSaveRenamePattern} currentPattern={renamePattern} files={filesForRenamePreview} />}
            {modalState.type === 'delete' && <ConfirmationModal isOpen={true} onCancel={() => setModalState({ type: 'none' })} onConfirm={() => handleDelete(modalState.fileId)} title="Potwierdź usunięcie">{`Czy na pewno chcesz usunąć ${modalState.fileId === 'all' ? 'wszystkie pliki' : modalState.fileId === 'selected' ? `${selectedFiles.length} zaznaczone pliki` : 'ten plik'} z kolejki?`}</ConfirmationModal>}
            {modalState.type === 'batch-edit' && <BatchEditModal isOpen={true} onClose={() => setModalState({ type: 'none' })} onSave={handleBatchEditSave} files={selectedFiles} />}
            {modalState.type === 'post-download' && <PostDownloadModal isOpen={true} onKeep={() => setModalState({ type: 'none' })} onRemove={handlePostDownloadRemove} count={modalState.count} />}
            {modalState.type === 'zoom-cover' && <AlbumCoverModal isOpen={true} onClose={() => setModalState({ type: 'none' })} imageUrl={modalState.imageUrl} />}
            {modalState.type === 'preview-changes' && <PreviewChangesModal isOpen={true} onCancel={() => setModalState({ type: 'none' })} onConfirm={modalState.onConfirm} title={modalState.title} previews={modalState.previews}>{modalState.confirmationText}</PreviewChangesModal>}
        </div>
    );
};

export default App;