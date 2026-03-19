
import React, { useState, useEffect } from 'react';

// Components
import FileDropzone from './components/FileDropzone';
import SettingsModal from './components/SettingsModal';
import RenameModal from './components/RenameModal';
import BatchEditModal from './components/BatchEditModal';
import PostDownloadModal from './components/PostDownloadModal';
import PreviewChangesModal from './components/PreviewChangesModal';
import DuplicateResolverModal from './components/DuplicateResolverModal';

// New Components (Library View)
import Sidebar from './components/Sidebar';
import TrackTable from './components/TrackTable';
import RightPanel from './components/RightPanel';
import PlayerDock from './components/PlayerDock';
import LibraryToolbar from './components/LibraryToolbar';
import WelcomeScreen from './components/WelcomeScreen';

// Hooks
import { useLibrary } from './hooks/useLibrary';
import { useSettings } from './hooks/useSettings';
import { useAIProcessing } from './hooks/useAIProcessing';

// Utils
import { applyTags, saveFileDirectly, isTagWritingSupported } from './utils/audioUtils';
import { ProcessingState, AudioFile } from './types';
import { findDuplicateSets } from './utils/duplicateUtils';
import { exportFilesToCsv } from './utils/csvUtils';

// Declare libs
declare const JSZip: any;
declare const saveAs: any;

const SUPPORTED_FORMATS = ['audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/flac', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/x-m4a', 'audio/aac', 'audio/x-ms-wma'];

type ModalState = 
  | { type: 'none' }
  | { type: 'settings' }
  | { type: 'rename' }
  | { type: 'batch-edit' }
  | { type: 'post-download'; count: number }
  | { type: 'preview-changes'; title: string; confirmationText: string; previews: any[]; onConfirm: () => void; }
  | { type: 'import' }
  | { type: 'duplicates'; sets: Map<string, AudioFile[]> };

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
    // --- State Management via Hooks ---
    const { 
        theme, setTheme, apiKeys, setApiKeys, aiProvider, setAiProvider, renamePattern, setRenamePattern 
    } = useSettings();

    const {
        files, setFiles, sortedFiles, selectedFileIds, activeFileId, activeFile, selectedFiles,
        isRestored, sortConfig, setSortConfig,
        addFiles, updateFile, removeFiles, toggleSelection, selectAll, clearSelection, activateFile,
        setIsRestored
    } = useLibrary(renamePattern);

    const { 
        analyzeBatch, isBatchAnalyzing 
    } = useAIProcessing(files, updateFile, apiKeys, aiProvider);

    // --- Local App State ---
    const [isSaving, setIsSaving] = useState(false);
    const [directoryHandle, setDirectoryHandle] = useState<any | null>(null);
    const [modalState, setModalState] = useState<ModalState>({ type: 'none' });

    // --- Handlers ---

    const handleFilesSelected = async (fileList: FileList) => {
        const filesToAdd = Array.from(fileList).map(f => ({ file: f }));
        await addFiles(filesToAdd);
    };

    const handleDirectoryConnect = async (handle: any) => {
        setIsRestored(false); // Reset 'Restored' flag when connecting real directory
        setDirectoryHandle(handle);
        setFiles([]); // Clear existing list for fresh import
        try {
            const filesToProcess = [];
            for await (const fileData of getFilesRecursively(handle)) {
                filesToProcess.push(fileData);
            }
            await addFiles(filesToProcess);
        } catch (error) {
            alert(`Błąd: ${error}`);
        }
    };
    
    const handleUrlSubmitted = async (url: string) => {
        try {
            const proxyUrl = 'https://api.allorigins.win/raw?url=';
            const response = await fetch(proxyUrl + encodeURIComponent(url));
            if (!response.ok) throw new Error("Network error");
            const blob = await response.blob();
            const file = new File([blob], 'remote.mp3', { type: blob.type });
            await addFiles([{ file }]);
        } catch(e) { alert("Błąd pobierania URL"); }
    };

    const handleDownloadOrSave = async () => {
        const targetFiles = selectedFiles.length > 0 ? selectedFiles : files;
        if (targetFiles.length === 0) return;

        // Reuse preview logic
        const previews = targetFiles.map(file => {
             const newName = file.newName || file.file.name;
             const oldName = file.webkitRelativePath || file.file.name;
             return { originalName: oldName, newName, isTooLong: newName.length > 255 };
        }).filter(p => p.originalName !== p.newName);

        const execute = () => executeDownloadOrSave(targetFiles);

        if (previews.length === 0) {
            await execute();
        } else {
            setModalState({
                type: 'preview-changes',
                title: directoryHandle ? 'Potwierdź zapis' : 'Potwierdź pobieranie',
                confirmationText: 'Pliki zostaną zmienione zgodnie z szablonem.',
                previews,
                onConfirm: () => {
                    setModalState({ type: 'none' });
                    setTimeout(execute, 50);
                }
            });
        }
    };

    const executeDownloadOrSave = async (targetFiles: AudioFile[]) => {
        if (directoryHandle) {
             setIsSaving(true);
             const ids = targetFiles.map(f => f.id);
             setFiles(files => files.map(f => ids.includes(f.id) ? { ...f, state: ProcessingState.DOWNLOADING } : f));
             
             for (const file of targetFiles) {
                 const res = await saveFileDirectly(directoryHandle, file);
                 if (res.success && res.updatedFile) {
                     updateFile(file.id, { ...res.updatedFile, state: ProcessingState.SUCCESS });
                 } else {
                     updateFile(file.id, { state: ProcessingState.ERROR, errorMessage: res.errorMessage });
                 }
             }
             setIsSaving(false);
             alert("Zapis zakończony.");
        } else {
             handleDownloadZip(targetFiles);
        }
    };

    const handleDownloadZip = async (targetFiles: AudioFile[]) => {
        setIsSaving(true);
        try {
             if (typeof JSZip === 'undefined' || typeof saveAs === 'undefined') throw new Error("Biblioteki ZIP nie zostały załadowane");
             const zip = new JSZip();
             
             for (const file of targetFiles) {
                  let blob: Blob = file.file;
                  
                  // Only try to apply tags if the format supports it (MP3, M4A).
                  // For FLAC, WAV, etc., we zip the original file but use the new name.
                  if (isTagWritingSupported(file.file)) {
                      try {
                          blob = await applyTags(file.file, file.fetchedTags || file.originalTags);
                      } catch (tagError) {
                          console.warn(`Skipping tagging for ZIP for ${file.file.name}:`, tagError);
                          // Fallback to original blob
                          blob = file.file;
                      }
                  }
                  
                  zip.file(file.newName || file.file.name, blob); 
             }
             
             const content = await zip.generateAsync({type:"blob"});
             saveAs(content, "music.zip");
             setModalState({ type: 'post-download', count: targetFiles.length });
        } catch(e) { 
            console.error(e);
            alert("Błąd tworzenia archiwum ZIP"); 
        }
        setIsSaving(false);
    };

    const handleFindDuplicates = () => {
        if (files.length < 2) {
            alert("Dodaj więcej plików, aby wyszukać duplikaty.");
            return;
        }
        const sets = findDuplicateSets(files);
        if (sets.size === 0) {
            alert("Nie znaleziono duplikatów w bibliotece.");
            return;
        }
        setModalState({ type: 'duplicates', sets });
    };

    const handleExportCsv = () => {
        if (files.length === 0) return;
        try {
            const csvContent = exportFilesToCsv(files);
            const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
            saveAs(blob, "lumbago_library_export.csv");
        } catch (e) {
            console.error("Export CSV failed", e);
            alert("Wystąpił błąd podczas eksportu CSV.");
        }
    };

    // --- Render ---

    return (
        <div className="flex h-screen bg-slate-50 dark:bg-slate-950 font-sans overflow-hidden">
            
            <Sidebar totalFiles={files.length} />

            <div className="flex-grow flex flex-col min-w-0">
                
                <LibraryToolbar 
                    onImport={() => setModalState({ type: 'import' })}
                    onSettings={() => setModalState({ type: 'settings' })}
                    // Analyzes everything that isn't successfully processed, OR files that are successful but missing BPM (incomplete analysis)
                    onAnalyzeAll={() => analyzeBatch(files.filter(f => f.state !== ProcessingState.SUCCESS || !f.fetchedTags?.bpm))}
                    onAnalyzeSelected={() => analyzeBatch(selectedFiles, false)}
                    // Force analysis with Web Search for selected files
                    onForceAnalyzeSelected={() => analyzeBatch(selectedFiles, true)}
                    onEdit={() => setModalState({ type: 'batch-edit' })}
                    onExport={() => handleDownloadOrSave()}
                    onDelete={() => {
                        if(confirm('Czy na pewno chcesz usunąć zaznaczone pliki?')) removeFiles(selectedFileIds);
                    }}
                    onClearAll={() => {
                        if(confirm('Wyczyścić całą bibliotekę?')) setFiles([]);
                    }}
                    onRename={() => setModalState({ type: 'rename' })}
                    onFindDuplicates={handleFindDuplicates}
                    onExportCsv={handleExportCsv}
                    
                    selectedCount={selectedFileIds.length}
                    totalCount={files.length}
                    allSelected={files.length > 0 && selectedFileIds.length === files.length}
                    onToggleSelectAll={() => selectedFileIds.length === files.length ? clearSelection() : selectAll()}
                    
                    theme={theme}
                    setTheme={setTheme}
                    isProcessing={isBatchAnalyzing || isSaving}
                    isDirectAccessMode={!!directoryHandle}
                    directoryName={directoryHandle?.name}
                    isRestored={isRestored}
                />

                {files.length === 0 ? (
                    <div className="flex-grow overflow-y-auto p-8 flex flex-col items-center justify-center">
                        <WelcomeScreen onDirectoryConnect={handleDirectoryConnect}>
                             <FileDropzone onFilesSelected={handleFilesSelected} onUrlSubmitted={handleUrlSubmitted} isProcessing={false} />
                        </WelcomeScreen>
                    </div>
                ) : (
                    <TrackTable 
                        files={sortedFiles} 
                        selectedFileIds={selectedFileIds}
                        activeFileId={activeFileId}
                        onSelect={toggleSelection}
                        onSelectAll={selectedFileIds.length === files.length ? clearSelection : selectAll}
                        onActivate={activateFile}
                        sortConfig={sortConfig}
                        onSort={setSortConfig}
                    />
                )}

                <PlayerDock activeFile={activeFile} />
            </div>

            <RightPanel 
                file={activeFile} 
                allFiles={files}
                onClose={() => activateFile(null as any)} 
                onRenamePatternSettings={() => setModalState({ type: 'rename' })}
            />

            {modalState.type === 'import' && (
                <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-10" onClick={() => setModalState({ type: 'none' })}>
                    <div className="bg-white dark:bg-slate-900 rounded-xl p-8 max-w-4xl w-full" onClick={e => e.stopPropagation()}>
                        <h2 className="text-2xl font-bold dark:text-white mb-6">Importuj utwory</h2>
                        <FileDropzone onFilesSelected={(f) => { handleFilesSelected(f); setModalState({ type: 'none' }); }} onUrlSubmitted={handleUrlSubmitted} isProcessing={false} />
                        <div className="mt-4 text-center">
                             <button onClick={() => setModalState({ type: 'none' })} className="text-slate-500 hover:text-white">Anuluj</button>
                        </div>
                    </div>
                </div>
            )}
            
            {/* Modals */}
            {modalState.type === 'settings' && <SettingsModal isOpen={true} onClose={() => setModalState({ type: 'none' })} onSave={(k, p) => { setApiKeys(k); setAiProvider(p); setModalState({type: 'none'}); }} currentKeys={apiKeys} currentProvider={aiProvider} />}
            {modalState.type === 'batch-edit' && <BatchEditModal isOpen={true} onClose={() => setModalState({ type: 'none' })} onSave={(tags) => { 
                const ids = selectedFileIds;
                ids.forEach(id => updateFile(id, { fetchedTags: { ...(files.find(f => f.id === id)?.fetchedTags || {}), ...tags } }));
                setModalState({ type: 'none' });
            }} files={selectedFiles} />}
            {modalState.type === 'preview-changes' && <PreviewChangesModal isOpen={true} {...modalState} onCancel={() => setModalState({type:'none'})} >{modalState.confirmationText}</PreviewChangesModal>}
            {modalState.type === 'post-download' && <PostDownloadModal isOpen={true} onRemove={() => { removeFiles(selectedFileIds); setModalState({type:'none'}); }} onKeep={() => setModalState({type:'none'})} count={modalState.count} />}
            {modalState.type === 'rename' && <RenameModal isOpen={true} onClose={() => setModalState({type: 'none'})} onSave={(pattern) => { setRenamePattern(pattern); setModalState({type: 'none'}); }} currentPattern={renamePattern} files={files} />}
            
            {modalState.type === 'duplicates' && (
                <DuplicateResolverModal 
                    isOpen={true}
                    onClose={() => setModalState({ type: 'none' })}
                    duplicateSets={modalState.sets}
                    onRemoveFiles={(idsToRemove) => {
                        removeFiles(idsToRemove);
                        setModalState({ type: 'none' });
                    }}
                />
            )}
        </div>
    );
};

export default App;
