import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import DashboardTab from './components/DashboardTab';
import ToastStack, { ToastItem } from './components/ToastStack';
import { AudioFile, ID3Tags, ProcessingState } from './types';
import { AIProvider, analyzeWithProviders, ApiKeys } from './services/aiService';
import { applyTags, readID3Tags, saveFileDirectly, isTagWritingSupported } from './utils/audioUtils';
import { generatePath } from './utils/filenameUtils';
import { sortFiles, SortKey } from './utils/sortingUtils';
import { exportFilesToCsv } from './utils/csvUtils';
import { SmartTagPipeline } from './services/smartTagPipeline';

declare const uuid: { v4: () => string };
declare const JSZip: any;
declare const saveAs: any;

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
  | { type: 'zoom-cover'; imageUrl: string }
  | { type: 'preview-changes'; title: string; confirmationText: string; previews: RenamePreview[]; onConfirm: () => void };

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
  retryCount?: number;
}

async function* getFilesRecursively(entry: any): AsyncGenerator<{ file: File; handle: any; path: string }> {
  if (entry.kind === 'file') {
    const file = await entry.getFile();
    if (SUPPORTED_FORMATS.includes(file.type)) {
      yield { file, handle: entry, path: entry.name };
    }
    return;
  }
  if (entry.kind === 'directory') {
    for await (const handle of entry.values()) {
      for await (const nestedFile of getFilesRecursively(handle)) {
        yield { ...nestedFile, path: `${entry.name}/${nestedFile.path}` };
      }
    }
  }
}

const App: React.FC = () => {
  const [files, setFiles] = useState<AudioFile[]>(() => {
    const saved = localStorage.getItem('audioFiles');
    if (!saved) return [];
    try {
      const parsed: SerializableAudioFile[] = JSON.parse(saved);
      return parsed.map((item) => ({
        ...item,
        file: new File([], item.fileName, { type: item.fileType }),
        handle: null,
      }));
    } catch {
      return [];
    }
  });
  const filesRef = useRef(files);
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
  const [activeTab, setActiveTab] = useState<string>(files.length ? 'dashboard' : 'scan');
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const pushToast = useCallback((item: Omit<ToastItem, 'id'>) => {
    const id = `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    setToasts((current) => [...current, { ...item, id }]);
    setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 4500);
  }, []);

  useEffect(() => {
    filesRef.current = files;
  }, [files]);

  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.documentElement.className = theme;
  }, [theme]);
  useEffect(() => localStorage.setItem('apiKeys', JSON.stringify(apiKeys)), [apiKeys]);
  useEffect(() => localStorage.setItem('aiProvider', aiProvider), [aiProvider]);
  useEffect(() => localStorage.setItem('sortKey', sortKey), [sortKey]);
  useEffect(() => localStorage.setItem('sortDirection', sortDirection), [sortDirection]);
  useEffect(() => localStorage.setItem('renamePattern', renamePattern), [renamePattern]);

  useEffect(() => {
    if (files.length === 0) {
      localStorage.removeItem('audioFiles');
      return;
    }
    const serializableFiles: SerializableAudioFile[] = files.map((file) => ({
      id: file.id,
      state: file.state,
      originalTags: file.originalTags,
      fetchedTags: file.fetchedTags,
      newName: file.newName,
      isSelected: file.isSelected,
      errorMessage: file.errorMessage,
      dateAdded: file.dateAdded,
      webkitRelativePath: file.webkitRelativePath,
      fileName: file.file.name,
      fileType: file.file.type,
      retryCount: file.retryCount,
    }));
    localStorage.setItem('audioFiles', JSON.stringify(serializableFiles));
  }, [files]);

  useEffect(() => {
    setFiles((current) =>
      current.map((file) => ({
        ...file,
        newName: generatePath(renamePattern, file.fetchedTags || file.originalTags, file.file.name),
      }))
    );
  }, [renamePattern]);

  const updateFileState = useCallback((id: string, updates: Partial<AudioFile>) => {
    setFiles((current) => current.map((file) => (file.id === id ? { ...file, ...updates } : file)));
  }, []);

  const selectedFiles = useMemo(() => files.filter((file) => file.isSelected), [files]);
  const allFilesSelected = useMemo(() => files.length > 0 && files.every((file) => file.isSelected), [files]);
  const sortedFiles = useMemo(() => sortFiles([...files], sortKey, sortDirection), [files, sortKey, sortDirection]);
  const modalFile = useMemo(() => (modalState.type === 'edit' ? files.find((file) => file.id === modalState.fileId) : undefined), [modalState, files]);
  const filesForRenamePreview = selectedFiles.length > 0 ? selectedFiles : files.slice(0, 5);

  const handleClearAndReset = () => {
    setFiles([]);
    setDirectoryHandle(null);
    setActiveTab('scan');
    pushToast({ type: 'info', title: 'Wyczyszczono listę', message: 'Kolejka plików została wyczyszczona.' });
  };

  const addFilesToQueue = useCallback(
    async (filesToAdd: { file: File; handle?: any; path?: string }[]) => {
      const validAudioFiles = filesToAdd.filter((item) => SUPPORTED_FORMATS.includes(item.file.type));
      if (validAudioFiles.length === 0) {
        pushToast({ type: 'error', title: 'Brak plików', message: 'Nie znaleziono obsługiwanych formatów audio.' });
        return;
      }
      const newAudioFiles: AudioFile[] = await Promise.all(
        validAudioFiles.map(async (item) => ({
          id: uuid.v4(),
          file: item.file,
          handle: item.handle,
          webkitRelativePath: item.path || item.file.webkitRelativePath,
          state: ProcessingState.PENDING,
          originalTags: await readID3Tags(item.file),
          dateAdded: Date.now(),
          retryCount: 0,
        }))
      );
      setFiles((current) => [...current, ...newAudioFiles]);
      setActiveTab('library');
      pushToast({ type: 'success', title: 'Import zakończony', message: `Dodano ${newAudioFiles.length} plików.` });
    },
    [pushToast]
  );

  const runSmartScan = useCallback(
    async (target: 'selected' | 'all', explicitIds?: string[]) => {
      const ids = explicitIds || (target === 'selected' ? selectedFiles.map((file) => file.id) : filesRef.current.map((file) => file.id));
      if (ids.length === 0) {
        pushToast({ type: 'info', title: 'Brak plików', message: 'Wybierz pliki do tagowania.' });
        return;
      }

      setIsBatchAnalyzing(true);
      const pipeline = new SmartTagPipeline({
        files: filesRef.current,
        directoryHandle,
        apiKeys,
        onFileUpdate: (fileId, patch) => updateFileState(fileId, patch),
      });

      const result = await pipeline.runSmartScan(target, ids);
      setIsBatchAnalyzing(false);
      pushToast({
        type: result.errors > 0 ? 'error' : 'success',
        title: 'Auto-Tag zakończony',
        message: `OK: ${result.success}, Błędy: ${result.errors}, Przetworzone: ${result.processed}`,
      });
    },
    [apiKeys, directoryHandle, pushToast, selectedFiles, updateFileState]
  );

  const retryTagging = useCallback(
    async (fileId: string) => {
      const pipeline = new SmartTagPipeline({
        files: filesRef.current,
        directoryHandle,
        apiKeys,
        onFileUpdate: (id, patch) => updateFileState(id, patch),
      });
      const run = await pipeline.retryTagging(fileId);
      if (!run) return;
      pushToast({
        type: run.status === 'SUCCESS' ? 'success' : 'error',
        title: run.status === 'SUCCESS' ? 'Ponowienie zakończone' : 'Ponowienie nieudane',
        message: run.status === 'SUCCESS' ? 'Plik został poprawnie otagowany.' : run.error?.message || 'Błąd retry.',
      });
    },
    [apiKeys, directoryHandle, pushToast, updateFileState]
  );

  const handleFilesSelected = async (selected: FileList) => {
    await addFilesToQueue(Array.from(selected).map((file) => ({ file })));
  };

  const handleDirectoryConnect = useCallback(
    async (handle: any) => {
      setDirectoryHandle(handle);
      const filesToProcess: { file: File; handle: any; path: string }[] = [];
      for await (const fileData of getFilesRecursively(handle)) {
        filesToProcess.push(fileData);
      }
      await addFilesToQueue(filesToProcess);
    },
    [addFilesToQueue]
  );

  const handleUrlSubmitted = async (url: string) => {
    if (!url) return;
    try {
      const response = await fetch(`https://api.allorigins.win/raw?url=${encodeURIComponent(url)}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const blob = await response.blob();
      const fileName = decodeURIComponent(new URL(url).pathname.split('/').pop() || 'remote_file.mp3');
      await addFilesToQueue([{ file: new File([blob], fileName, { type: blob.type }) }]);
    } catch (error) {
      pushToast({ type: 'error', title: 'Import URL nieudany', message: error instanceof Error ? error.message : 'Unknown URL error' });
      throw error;
    }
  };

  const handleSelectionChange = (fileId: string, isSelected: boolean) => updateFileState(fileId, { isSelected });
  const handleToggleSelectAll = () => setFiles((current) => current.map((file) => ({ ...file, isSelected: !allFilesSelected })));

  const handleDelete = (fileId: string | 'selected' | 'all') => {
    if (fileId === 'all') {
      handleClearAndReset();
    } else if (fileId === 'selected') {
      setFiles((current) => current.filter((file) => !file.isSelected));
    } else {
      setFiles((current) => current.filter((file) => file.id !== fileId));
    }
    setModalState({ type: 'none' });
  };

  const openDeleteModal = (id: string | 'selected' | 'all') => {
    if (id === 'selected' && selectedFiles.length === 0) {
      pushToast({ type: 'info', title: 'Brak zaznaczenia', message: 'Zaznacz pliki do usunięcia.' });
      return;
    }
    setModalState({ type: 'delete', fileId: id });
  };

  const handleSaveSettings = (keys: ApiKeys, provider: AIProvider) => {
    setApiKeys(keys);
    setAiProvider(provider);
    setModalState({ type: 'none' });
    pushToast({ type: 'success', title: 'Ustawienia zapisane', message: 'Zapisano konfigurację providerów AI.' });
  };

  const handleSaveTags = (fileId: string, tags: ID3Tags) => {
    updateFileState(fileId, { fetchedTags: tags });
    setModalState({ type: 'none' });
  };

  const handleApplyTags = async (fileId: string, tags: ID3Tags) => {
    if (!directoryHandle) return;
    const file = filesRef.current.find((candidate) => candidate.id === fileId);
    if (!file || !file.handle) return;
    setSavingFileId(fileId);
    try {
      const result = await saveFileDirectly(directoryHandle, { ...file, fetchedTags: tags });
      if (!result.success || !result.updatedFile) {
        throw new Error(result.errorMessage || 'Write failed');
      }
      updateFileState(fileId, { ...result.updatedFile, state: ProcessingState.SUCCESS, fetchedTags: tags });
      setModalState({ type: 'none' });
      pushToast({ type: 'success', title: 'Tagi zapisane', message: result.updatedFile.file.name });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Write failed';
      updateFileState(fileId, { state: ProcessingState.ERROR, errorMessage: message, fetchedTags: tags });
      pushToast({ type: 'error', title: 'Zapis nieudany', message });
    } finally {
      setSavingFileId(null);
    }
  };

  const handleManualSearch = async (query: string, file: AudioFile) => {
    updateFileState(file.id, { state: ProcessingState.PROCESSING });
    try {
      const providerResults = await analyzeWithProviders(`Manual query: ${query}\nCurrent tags: ${JSON.stringify(file.fetchedTags || file.originalTags)}`, apiKeys);
      const successful = providerResults.filter((item) => !item.error).sort((a, b) => b.confidence - a.confidence);
      const best = successful[0];
      if (!best) throw new Error('No provider returned valid payload');
      updateFileState(file.id, {
        state: ProcessingState.SUCCESS,
        fetchedTags: { ...(file.fetchedTags || file.originalTags), ...best.tags },
      });
      pushToast({ type: 'success', title: 'Manual search', message: `${best.provider}: znaleziono aktualizacje tagów.` });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Manual search failed';
      updateFileState(file.id, { state: ProcessingState.ERROR, errorMessage: message });
      pushToast({ type: 'error', title: 'Manual search', message });
      throw error;
    }
  };

  const handleSaveRenamePattern = (newPattern: string) => {
    const previews = filesForRenamePreview.map((file) => ({
      originalName: file.webkitRelativePath || file.file.name,
      newName: generatePath(newPattern, file.fetchedTags || file.originalTags, file.file.name),
      isTooLong: (file.newName || '').length > 255,
    }));
    setModalState({
      type: 'preview-changes',
      title: 'Potwierdź zmianę szablonu',
      confirmationText: 'Nowy szablon zostanie zastosowany. Czy kontynuować?',
      previews,
      onConfirm: () => {
        setRenamePattern(newPattern);
        setModalState({ type: 'none' });
      },
    });
  };

  const handleBatchEditSave = (tagsToApply: Partial<ID3Tags>) => {
    setFiles((current) =>
      current.map((file) => {
        if (!file.isSelected) return file;
        const nextTags = { ...(file.fetchedTags || {}), ...tagsToApply };
        return { ...file, fetchedTags: nextTags };
      })
    );
    setModalState({ type: 'none' });
  };

  const executeDownloadOrSave = async () => {
    const filesToSave = selectedFiles;
    if (filesToSave.length === 0) {
      pushToast({ type: 'info', title: 'Brak plików', message: 'Wybierz pliki do zapisu lub pobrania.' });
      return;
    }

    setIsSaving(true);
    try {
      if (directoryHandle) {
        const ids = filesToSave.map((file) => file.id);
        setFiles((current) => current.map((file) => (ids.includes(file.id) ? { ...file, state: ProcessingState.DOWNLOADING } : file)));

        const results = await Promise.all(filesToSave.map((file) => saveFileDirectly(directoryHandle, file)));
        let ok = 0;
        results.forEach((result, idx) => {
          const source = filesToSave[idx];
          if (result.success && result.updatedFile) {
            ok += 1;
            updateFileState(source.id, { ...result.updatedFile, state: ProcessingState.SUCCESS, isSelected: false });
          } else {
            updateFileState(source.id, { state: ProcessingState.ERROR, errorMessage: result.errorMessage || 'Save failed' });
          }
        });
        pushToast({ type: ok === filesToSave.length ? 'success' : 'error', title: 'Zapis zakończony', message: `Sukces: ${ok}/${filesToSave.length}` });
      } else {
        const zip = new JSZip();
        for (const file of filesToSave) {
          const finalName = generatePath(renamePattern, file.fetchedTags || file.originalTags, file.file.name) || file.file.name;
          if (isTagWritingSupported(file.file) && file.fetchedTags) {
            const blob = await applyTags(file.file, file.fetchedTags);
            zip.file(finalName, blob);
          } else {
            zip.file(finalName, file.file);
          }
        }
        const zipBlob = await zip.generateAsync({ type: 'blob' });
        saveAs(zipBlob, 'tagged-music.zip');
        setModalState({ type: 'post-download', count: filesToSave.length });
        pushToast({ type: 'success', title: 'Pobieranie gotowe', message: `Spakowano ${filesToSave.length} plików.` });
      }
    } catch (error) {
      pushToast({ type: 'error', title: 'Błąd zapisu', message: error instanceof Error ? error.message : 'Write failed' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadOrSave = async () => {
    const previews = selectedFiles
      .map((file) => ({
        originalName: file.webkitRelativePath || file.file.name,
        newName: file.newName || file.file.name,
        isTooLong: (file.newName || file.file.name).length > 255,
      }))
      .filter((preview) => preview.originalName !== preview.newName);
    if (!previews.length) {
      await executeDownloadOrSave();
      return;
    }
    setModalState({
      type: 'preview-changes',
      title: directoryHandle ? 'Potwierdź zapis ze zmianą nazw' : 'Potwierdź pobranie ze zmianą nazw',
      confirmationText: 'Nazwy plików zostaną zmienione przed zapisem.',
      previews,
      onConfirm: () => {
        setModalState({ type: 'none' });
        setTimeout(() => void executeDownloadOrSave(), 50);
      },
    });
  };

  const handleExportCsv = () => {
    if (!files.length) {
      pushToast({ type: 'info', title: 'Brak danych', message: 'Nie ma plików do eksportu CSV.' });
      return;
    }
    const csvData = exportFilesToCsv(files);
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `id3-tagger-export-${new Date().toISOString().replace(/[:.]/g, '-')}.csv`);
    pushToast({ type: 'success', title: 'CSV wygenerowany', message: 'Wyeksportowano listę plików.' });
  };

  const handlePostDownloadRemove = () => {
    setFiles((current) => current.filter((file) => !file.isSelected));
    setModalState({ type: 'none' });
  };

  const handleDirectoryPicker = async () => {
    try {
      if (!('showDirectoryPicker' in window)) {
        pushToast({ type: 'error', title: 'Brak wsparcia API', message: 'Ta przeglądarka nie obsługuje File System Access API.' });
        return;
      }
      const handle = await (window as any).showDirectoryPicker();
      await handleDirectoryConnect(handle);
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        pushToast({ type: 'error', title: 'Błąd wyboru folderu', message: error.message });
      }
    }
  };

  const tabs: Tab[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      component: <DashboardTab files={files} isRunning={isBatchAnalyzing} onSmartScan={() => void runSmartScan('all')} onOpenLibrary={() => setActiveTab('library')} />,
    },
    {
      id: 'library',
      label: 'Biblioteka',
      component: (
        <LibraryTab
          files={files}
          sortedFiles={sortedFiles}
          selectedFiles={selectedFiles}
          allFilesSelected={allFilesSelected}
          isBatchAnalyzing={isBatchAnalyzing}
          isSaving={isSaving}
          directoryHandle={directoryHandle}
          isRestored={false}
          onToggleSelectAll={handleToggleSelectAll}
          onBatchAnalyze={() => void runSmartScan('selected')}
          onBatchAnalyzeAll={() => void runSmartScan('all')}
          onDownloadOrSave={() => void handleDownloadOrSave()}
          onBatchEdit={() => setModalState({ type: 'batch-edit' })}
          onSingleItemEdit={(id) => setModalState({ type: 'edit', fileId: id })}
          onRename={() => setModalState({ type: 'rename' })}
          onExportCsv={handleExportCsv}
          onDeleteItem={openDeleteModal}
          onClearAll={() => openDeleteModal('all')}
          onProcessFile={(file) => void runSmartScan('selected', [file.id])}
          onRetryFile={(fileId) => void retryTagging(fileId)}
          onSelectionChange={handleSelectionChange}
          onTabChange={setActiveTab}
        />
      ),
    },
    {
      id: 'scan',
      label: 'Import / Skan',
      component: <ScanTab onFilesSelected={handleFilesSelected} onUrlSubmitted={handleUrlSubmitted} onDirectoryConnect={handleDirectoryConnect} isProcessing={isBatchAnalyzing} />,
    },
    { id: 'tagger', label: 'SMART AI Skan', component: <PlaceholderTab title="SMART AI Skan działa z Dashboard i Biblioteki" /> },
    { id: 'duplicates', label: 'Wyszukiwarka Duplikatów', component: <PlaceholderTab title="Wyszukiwarka Duplikatów" /> },
    { id: 'converter', label: 'Konwerter XML', component: <PlaceholderTab title="Konwerter XML" /> },
  ];

  return (
    <div className="bg-slate-50 dark:bg-slate-900 min-h-screen font-sans text-slate-800 dark:text-white transition-colors duration-300">
      <ToastStack items={toasts} onDismiss={(id) => setToasts((current) => current.filter((item) => item.id !== id))} />
      <main className="container mx-auto px-4 py-8">
        <header className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Lumbago Music AI</h1>
          <div className="flex items-center space-x-2">
            <ThemeToggle theme={theme} setTheme={setTheme} />
            <button onClick={() => setModalState({ type: 'settings' })} className="p-2 rounded-full text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" title="Ustawienia">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </header>

        <MainToolbar onTabChange={setActiveTab} onDirectorySelect={handleDirectoryPicker} />
        <TabbedInterface tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
        <Footer />
      </main>

      {modalState.type === 'settings' && (
        <SettingsModal
          isOpen
          onClose={() => setModalState({ type: 'none' })}
          onSave={handleSaveSettings}
          currentKeys={apiKeys}
          currentProvider={aiProvider}
        />
      )}
      {modalState.type === 'edit' && modalFile && (
        <EditTagsModal
          isOpen
          onClose={() => setModalState({ type: 'none' })}
          onSave={(tags) => handleSaveTags(modalFile.id, tags)}
          onApply={(tags) => void handleApplyTags(modalFile.id, tags)}
          isApplying={savingFileId === modalFile.id}
          isDirectAccessMode={!!directoryHandle}
          file={modalFile}
          onManualSearch={handleManualSearch}
          onZoomCover={(imageUrl) => setModalState({ type: 'zoom-cover', imageUrl })}
        />
      )}
      {modalState.type === 'rename' && <RenameModal isOpen onClose={() => setModalState({ type: 'none' })} onSave={handleSaveRenamePattern} currentPattern={renamePattern} files={filesForRenamePreview} />}
      {modalState.type === 'delete' && (
        <ConfirmationModal isOpen onCancel={() => setModalState({ type: 'none' })} onConfirm={() => handleDelete(modalState.fileId)} title="Potwierdź usunięcie">
          {`Czy na pewno chcesz usunąć ${
            modalState.fileId === 'all' ? 'wszystkie pliki' : modalState.fileId === 'selected' ? `${selectedFiles.length} zaznaczone pliki` : 'ten plik'
          } z kolejki?`}
        </ConfirmationModal>
      )}
      {modalState.type === 'batch-edit' && <BatchEditModal isOpen onClose={() => setModalState({ type: 'none' })} onSave={handleBatchEditSave} files={selectedFiles} />}
      {modalState.type === 'post-download' && <PostDownloadModal isOpen onKeep={() => setModalState({ type: 'none' })} onRemove={handlePostDownloadRemove} count={modalState.count} />}
      {modalState.type === 'zoom-cover' && <AlbumCoverModal isOpen onClose={() => setModalState({ type: 'none' })} imageUrl={modalState.imageUrl} />}
      {modalState.type === 'preview-changes' && (
        <PreviewChangesModal isOpen onCancel={() => setModalState({ type: 'none' })} onConfirm={modalState.onConfirm} title={modalState.title} previews={modalState.previews}>
          {modalState.confirmationText}
        </PreviewChangesModal>
      )}
    </div>
  );
};

export default App;
