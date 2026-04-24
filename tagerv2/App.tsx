import React, { useState, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

// Components
import FileDropzone from "./components/FileDropzone";
import SettingsModal from "./components/SettingsModal";
import RenameModal from "./components/RenameModal";
import BatchEditModal from "./components/BatchEditModal";
import PostDownloadModal from "./components/PostDownloadModal";
import PreviewChangesModal from "./components/PreviewChangesModal";
import DuplicateResolverModal from "./components/DuplicateResolverModal";
import XmlConverterModal from "./components/XmlConverterModal";
import SmartPlaylistModal from "./components/SmartPlaylistModal";
import SmartTaggerModal from "./components/SmartTaggerModal";
import ToastContainer, { Toast, ToastType } from "./components/ToastContainer";
import Dashboard from "./components/Dashboard";
import MediaBrowser from "./components/MediaBrowser";
import EditTagsModal from "./components/EditTagsModal";

// Library View Components
import Sidebar from "./components/Sidebar";
import TrackTable from "./components/TrackTable";
import RightPanel from "./components/RightPanel";
import PlayerDock from "./components/PlayerDock";
import LibraryToolbar from "./components/LibraryToolbar";
import WelcomeScreen from "./components/WelcomeScreen";
import ContextMenu, { ContextMenuAction } from "./components/ContextMenu";

// Hooks
import { useLibrary } from "./hooks/useLibrary";
import { useSettings } from "./hooks/useSettings";
import { useAIProcessing } from "./hooks/useAIProcessing";

// Utils
import {
  applyTags,
  saveFileDirectly,
  isTagWritingSupported,
} from "./utils/audioUtils";
import { ProcessingState, AudioFile } from "./types";
import { findDuplicateSets } from "./utils/duplicateUtils";
import { exportFilesToCsv } from "./utils/csvUtils";

declare const JSZip: any;
declare const saveAs: any;

const SUPPORTED_FORMATS = [
  "audio/mpeg",
  "audio/mp3",
  "audio/mp4",
  "audio/flac",
  "audio/wav",
  "audio/ogg",
  "audio/m4a",
  "audio/x-m4a",
  "audio/aac",
  "audio/x-ms-wma",
];

type ModalState =
  | { type: "none" }
  | { type: "settings" }
  | { type: "rename" }
  | { type: "batch-edit" }
  | { type: "post-download"; count: number }
  | {
      type: "preview-changes";
      title: string;
      confirmationText: string;
      previews: any[];
      onConfirm: () => void;
    }
  | { type: "import" }
  | { type: "duplicates"; sets: Map<string, AudioFile[]> }
  | { type: "xml-converter" }
  | { type: "smart-playlist" }
  | { type: "smart-tagger"; fileId: string };

async function* getFilesRecursively(
  entry: any,
  path = "",
): AsyncGenerator<{ file: File; handle: any; path: string }> {
  if (entry.kind === "file") {
    try {
      const file = await entry.getFile();
      const lowerName = file.name.toLowerCase();
      const hasAudioExt = [
        ".mp3",
        ".wav",
        ".flac",
        ".ogg",
        ".m4a",
        ".aac",
        ".wma",
      ].some((ext) => lowerName.endsWith(ext));

      if (SUPPORTED_FORMATS.includes(file.type) || hasAudioExt) {
        yield { file, handle: entry, path: path + entry.name };
      }
    } catch (e) {
      console.warn(`Nie udało się odczytać pliku: ${entry.name}`, e);
    }
  } else if (entry.kind === "directory") {
    const newPath = path + entry.name + "/";
    try {
      for await (const handle of entry.values()) {
        yield* getFilesRecursively(handle, newPath);
      }
    } catch (e) {
      console.warn(`Nie udało się otworzyć katalogu: ${entry.name}`, e);
    }
  }
}

const App: React.FC = () => {
  const {
    theme,
    setTheme,
    apiKeys,
    setApiKeys,
    aiProvider,
    setAiProvider,
    renamePattern,
    setRenamePattern,
    analysisSettings,
    setAnalysisSettings,
  } = useSettings();
  const {
    files,
    setFiles,
    paginatedFiles,
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
    selectAll,
    clearSelection,
    activateFile,
    setIsRestored,
    filters,
    setFilters,
    availableGenres,
    playlists,
    createPlaylist,
    addToPlaylist,
    currentPage,
    totalPages,
    setCurrentPage,
    popularTags,
  } = useLibrary(renamePattern);

  const { analyzeBatch, isBatchAnalyzing } = useAIProcessing(
    files,
    updateFile,
    apiKeys,
    aiProvider,
    analysisSettings,
  );

  const [isSaving, setIsSaving] = useState(false);
  const [directoryHandle, setDirectoryHandle] = useState<any | null>(null);
  const [modalState, setModalState] = useState<ModalState>({ type: "none" });
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");
  const [showFilters, setShowFilters] = useState(false);
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    targetId: string;
  } | null>(null);

  const addToast = useCallback((message: string, type: ToastType = "info") => {
    const id = uuidv4();
    setToasts((prev) => [...prev, { id, message, type }]);
  }, []);

  const removeToast = useCallback(
    (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id)),
    [],
  );

  // Handlers
  const handleFilesSelected = async (fileList: FileList) => {
    const filesToAdd = Array.from(fileList).map((f) => ({ file: f }));
    await addFiles(filesToAdd);
    addToast(`Dodano ${filesToAdd.length} plików`, "success");
  };

  const handleDirectoryConnect = async (handle: any) => {
    setIsRestored(false);
    setDirectoryHandle(handle);
    setFiles([]);

    let count = 0;
    addToast("Skanowanie folderu...", "info");

    try {
      const filesToProcess: { file: File; handle: any; path: string }[] = [];

      for await (const fileData of getFilesRecursively(handle, "")) {
        filesToProcess.push(fileData);
        count++;
        if (filesToProcess.length >= 50) {
          await addFiles([...filesToProcess]);
          filesToProcess.length = 0;
        }
      }

      if (filesToProcess.length > 0) {
        await addFiles(filesToProcess);
      }

      addToast(`Wczytano ${count} plików z folderu: ${handle.name}`, "success");
    } catch (error: any) {
      console.error(error);
      addToast(`Błąd odczytu folderu: ${error.message}`, "error");
    }
  };

  const handleUrlSubmitted = async (url: string) => {
    try {
      const proxyUrl = "https://api.allorigins.win/raw?url=";
      const response = await fetch(proxyUrl + encodeURIComponent(url));
      if (!response.ok) throw new Error("Network error");
      const blob = await response.blob();
      const file = new File([blob], "remote.mp3", { type: blob.type });
      await addFiles([{ file }]);
      addToast("Pobrano plik z URL", "success");
    } catch (e) {
      addToast("Błąd pobierania URL", "error");
    }
  };

  const handleDownloadOrSave = async () => {
    const targetFiles = selectedFiles.length > 0 ? selectedFiles : files;
    if (targetFiles.length === 0) return;

    const previews = targetFiles
      .map((file) => {
        const newName = file.newName || file.file.name;
        const oldName = file.webkitRelativePath || file.file.name;
        return {
          originalName: oldName,
          newName,
          isTooLong: newName.length > 255,
        };
      })
      .filter((p) => p.originalName !== p.newName);

    const execute = () => executeDownloadOrSave(targetFiles);

    if (previews.length === 0) {
      await execute();
    } else {
      setModalState({
        type: "preview-changes",
        title: directoryHandle ? "Potwierdź zapis" : "Potwierdź pobieranie",
        confirmationText: "Pliki zostaną zmienione zgodnie z szablonem.",
        previews,
        onConfirm: () => {
          setModalState({ type: "none" });
          setTimeout(execute, 50);
        },
      });
    }
  };

  const executeDownloadOrSave = async (targetFiles: AudioFile[]) => {
    if (directoryHandle) {
      setIsSaving(true);
      const ids = targetFiles.map((f) => f.id);
      setFiles((files) =>
        files.map((f) =>
          ids.includes(f.id) ? { ...f, state: ProcessingState.DOWNLOADING } : f,
        ),
      );

      let successCount = 0;
      let errorCount = 0;

      for (const file of targetFiles) {
        const res = await saveFileDirectly(directoryHandle, file);
        if (res.success && res.updatedFile) {
          updateFile(file.id, {
            ...res.updatedFile,
            state: ProcessingState.SUCCESS,
          });
          successCount++;
        } else {
          updateFile(file.id, {
            state: ProcessingState.ERROR,
            errorMessage: res.errorMessage,
          });
          errorCount++;
        }
      }
      setIsSaving(false);
      if (errorCount > 0)
        addToast(
          `Zapisano ${successCount} plików. Błędy: ${errorCount}`,
          "info",
        );
      else addToast("Zapis zakończony pomyślnie.", "success");
    } else {
      handleDownloadZip(targetFiles);
    }
  };

  const handleDownloadZip = async (targetFiles: AudioFile[]) => {
    setIsSaving(true);
    try {
      if (typeof JSZip === "undefined" || typeof saveAs === "undefined")
        throw new Error("Biblioteki ZIP nie zostały załadowane");
      const zip = new JSZip();

      for (const file of targetFiles) {
        let blob: Blob = file.file;
        if (isTagWritingSupported(file.file)) {
          try {
            blob = await applyTags(
              file.file,
              file.fetchedTags || file.originalTags,
            );
          } catch (tagError) {
            console.warn(
              `Skipping tagging for ZIP for ${file.file.name}:`,
              tagError,
            );
            blob = file.file;
          }
        }
        zip.file(file.newName || file.file.name, blob);
      }

      const content = await zip.generateAsync({ type: "blob" });
      saveAs(content, "music.zip");
      setModalState({ type: "post-download", count: targetFiles.length });
    } catch (e) {
      console.error(e);
      addToast("Błąd tworzenia archiwum ZIP", "error");
    }
    setIsSaving(false);
  };

  const handleFindDuplicates = () => {
    if (files.length < 2) {
      addToast("Dodaj więcej plików, aby wyszukać duplikaty.", "info");
      return;
    }
    const sets = findDuplicateSets(files);
    if (sets.size === 0) {
      addToast("Nie znaleziono duplikatów w bibliotece.", "success");
      return;
    }
    setModalState({ type: "duplicates", sets });
  };

  const handleExportCsv = () => {
    if (files.length === 0) return;
    try {
      const csvContent = exportFilesToCsv(files);
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
      saveAs(blob, "lumbago_library_export.csv");
      addToast("Wyeksportowano plik CSV", "success");
    } catch (e) {
      console.error("Export CSV failed", e);
      addToast("Wystąpił błąd podczas eksportu CSV.", "error");
    }
  };

  const handleCreatePlaylist = () => {
    const name = prompt("Podaj nazwę nowej playlisty:");
    if (name && name.trim()) {
      createPlaylist(name.trim());
      addToast(`Utworzono playlistę "${name}"`, "success");
    }
  };

  const handleContextMenu = (e: React.MouseEvent, fileId: string) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, targetId: fileId });
    if (!selectedFileIds.includes(fileId)) toggleSelection(fileId, false);
  };

  const getContextMenuActions = (): ContextMenuAction[] => {
    if (!contextMenu) return [];
    const isMultiSelect = selectedFileIds.length > 1;
    const targetFile = files.find((f) => f.id === contextMenu.targetId);
    const filesToAddIds =
      selectedFileIds.length > 0 ? selectedFileIds : [contextMenu.targetId];

    return [
      {
        label: "Smart Tag (Ten utwór)",
        icon: (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-[var(--accent-primary)]"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
              clipRule="evenodd"
            />
          </svg>
        ),
        onClick: () =>
          setModalState({ type: "smart-tagger", fileId: contextMenu.targetId }),
        disabled: isMultiSelect,
      },
      {
        label: isMultiSelect
          ? `Przetwarzaj zaznaczone (${selectedFileIds.length})`
          : "Przetwarzaj (AI Batch)",
        icon: (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-[var(--accent-primary)]"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
            <path
              fillRule="evenodd"
              d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        ),
        onClick: () =>
          analyzeBatch(
            selectedFileIds.length > 0
              ? selectedFiles
              : targetFile
                ? [targetFile]
                : [],
          ),
        disabled: isBatchAnalyzing,
      },
      {
        label: "Edytuj Tagi",
        icon: (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-[var(--text-secondary)]"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
        ),
        onClick: () => {
          if (selectedFileIds.length > 1) {
            setModalState({ type: "batch-edit" });
          } else if (targetFile) {
            setModalState({ type: "edit-tags", fileId: targetFile.id });
          }
        },
      },
      {
        label: "Dodaj do Playlisty",
        icon: (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-[var(--accent-primary)]"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
        ),
        onClick: () => {},
        subMenu:
          playlists.length > 0
            ? playlists.map((pl) => ({
                label: pl.name,
                icon: (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4 text-[var(--text-secondary)]"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
                  </svg>
                ),
                onClick: () => {
                  addToPlaylist(pl.id, filesToAddIds);
                  addToast(`Dodano do playlisty "${pl.name}"`, "success");
                },
              }))
            : [
                {
                  label: "Brak playlist (Utwórz nową)",
                  icon: (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 text-[var(--text-secondary)]"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ),
                  onClick: handleCreatePlaylist,
                },
              ],
      },
      {
        label: "Usuń",
        icon: (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-red-500"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        ),
        onClick: () => {
          if (confirm("Usunąć?")) {
            removeFiles(filesToAddIds);
            addToast("Usunięto pliki", "info");
          }
        },
        isDanger: true,
        divider: true,
      },
    ];
  };

  const handlePlay = (file: AudioFile) => {
    activateFile(file.id);
  };

  // --- Main Render ---
  const isDashboard = filters.playlistId === "dashboard";
  const isBrowser = filters.playlistId === "browser";

  return (
    <div className="flex h-screen bg-[var(--bg-base)] text-white font-sans overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="fixed top-[-10%] right-[-10%] w-[50%] h-[50%] bg-[var(--accent-cyan)]/5 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="fixed bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-[var(--accent-magenta)]/5 rounded-full blur-[100px] pointer-events-none"></div>

      <Sidebar
        activePlaylistId={filters.playlistId || null}
        onPlaylistSelect={(id) => setFilters((prev) => ({ ...prev, playlistId: id }))}
        onShowRecentlyAdded={() => {
          setSortConfig([{ key: "dateAdded", direction: "desc" }]);
          setFilters((prev) => ({ ...prev, playlistId: null }));
          addToast("Pokaż ostatnio dodane", "info");
        }}
        onShowDuplicates={handleFindDuplicates}
        onSettings={() => setModalState({ type: "settings" })}
      />

      <div className="flex-grow flex flex-col min-w-0 relative z-10">
        <LibraryToolbar
          onImport={() => setModalState({ type: "import" })}
          onSettings={() => setModalState({ type: "settings" })}
          onAnalyzeAll={() => analyzeBatch(files.filter(f => f.state !== ProcessingState.PROCESSING), true)}
          onAnalyzeSelected={() => analyzeBatch(selectedFiles, true)}
          onForceAnalyzeSelected={() => analyzeBatch(selectedFiles, true)}
          onEdit={() => setModalState({ type: "batch-edit" })}
          onExport={() => handleDownloadOrSave()}
          onDelete={() => {
            if (confirm("Usunąć zaznaczone?")) {
              removeFiles(selectedFileIds);
              addToast("Usunięto pliki", "info");
            }
          }}
          onClearAll={() => {
            if (confirm("Wyczyścić bibliotekę?")) {
              setFiles([]);
              addToast("Wyczyszczono bibliotekę", "success");
            }
          }}
          onRename={() => setModalState({ type: "rename" })}
          onFindDuplicates={handleFindDuplicates}
          onExportCsv={handleExportCsv}
          onConvertXml={() => setModalState({ type: "xml-converter" })}
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
          searchQuery={filters.search}
          onSearchChange={(q) => setFilters((prev) => ({ ...prev, search: q }))}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          showFilters={showFilters}
          onToggleFilters={() => setShowFilters(!showFilters)}
        />

        <div className="flex-grow flex overflow-hidden">
           {isDashboard ? (
             <Dashboard 
               totalFiles={files.length}
               onImport={() => setModalState({ type: "import" })}
               onAnalyzeAll={() => analyzeBatch(files.filter(f => f.state !== ProcessingState.PROCESSING), true)}
               onFindDuplicates={handleFindDuplicates}
               onBatchEdit={() => setModalState({ type: "batch-edit" })}
             />
           ) : isBrowser ? (
             <MediaBrowser 
               directoryHandle={directoryHandle}
               files={files}
               onPlay={handlePlay}
               onSelectEntries={(ids) => setSelectedFileIds(ids)}
               onContextMenu={handleContextMenu}
               popularTags={popularTags}
               onTagClick={(tag) => setFilters({ ...filters, search: tag })}
             />
           ) : files.length === 0 ? (
             <div className="flex-grow flex flex-col items-center justify-center p-12">
                <WelcomeScreen onDirectoryConnect={handleDirectoryConnect}>
                  <FileDropzone
                    onFilesSelected={handleFilesSelected}
                    onUrlSubmitted={handleUrlSubmitted}
                    isProcessing={false}
                  />
                </WelcomeScreen>
             </div>
           ) : (
             <div className="flex-grow overflow-hidden">
                <TrackTable
                  files={paginatedFiles}
                  selectedFileIds={selectedFileIds}
                  activeFileId={activeFileId}
                  onSelect={toggleSelection}
                  onActivate={activateFile}
                  sortConfig={sortConfig}
                  onSort={setSortConfig}
                  onContextMenu={handleContextMenu}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={setCurrentPage}
                />
             </div>
           )}

           {/* Context Menu */}
           {contextMenu && (
             <ContextMenu
               x={contextMenu.x}
               y={contextMenu.y}
               actions={getContextMenuActions()}
               onClose={() => setContextMenu(null)}
             />
           )}
           
          {/* Panels */}
          {showFilters && (
            <RightPanel 
              isFilterView
              file={null}
              allFiles={files}
              onClose={() => setShowFilters(false)}
              onRenamePatternSettings={() => {}}
              filters={filters}
              onFilterChange={setFilters}
              availableGenres={availableGenres}
              popularTags={popularTags}
            />
          )}
          
          {activeFileId && !showFilters && (
            <RightPanel 
              file={activeFile}
              allFiles={files}
              onClose={() => activateFile(null as any)}
              onRenamePatternSettings={() => setModalState({ type: "rename" })}
              onActivateFile={activateFile}
              popularTags={popularTags}
            />
          )}
        </div>

        <PlayerDock activeFile={activeFile} />
      </div>

      <ToastContainer toasts={toasts} removeToast={removeToast} />

      {/* Modals Container */}
      {modalState.type !== "none" && (
        <>
          {modalState.type === "import" && (
            <div
              className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-10 animate-fade-in"
              onClick={() => setModalState({ type: "none" })}
            >
              <div
                className="glass-panel rounded-none p-8 max-w-4xl w-full"
                onClick={(e) => e.stopPropagation()}
              >
                <h2 className="text-2xl font-bold text-white mb-6">
                  Importuj utwory
                </h2>
                <FileDropzone
                  onFilesSelected={(f) => {
                    handleFilesSelected(f);
                    setModalState({ type: "none" });
                  }}
                  onUrlSubmitted={handleUrlSubmitted}
                  isProcessing={false}
                />
                <div className="mt-4 text-center">
                  <button
                    onClick={() => setModalState({ type: "none" })}
                    className="text-[var(--text-secondary)] hover:text-white transition-colors"
                  >
                    Anuluj
                  </button>
                </div>
              </div>
            </div>
          )}
          {modalState.type === "settings" && (
            <SettingsModal
              isOpen={true}
              onClose={() => setModalState({ type: "none" })}
              onSave={(k, p, as) => {
                setApiKeys(k);
                setAiProvider(p);
                setAnalysisSettings(as);
                setModalState({ type: "none" });
                addToast("Zapisano ustawienia", "success");
              }}
              currentKeys={apiKeys}
              currentProvider={aiProvider}
              currentAnalysisSettings={analysisSettings}
            />
          )}
          {modalState.type === "batch-edit" && (
            <BatchEditModal
              isOpen={true}
              onClose={() => setModalState({ type: "none" })}
              onSave={(tags) => {
                selectedFileIds.forEach((id) =>
                  updateFile(id, {
                    fetchedTags: {
                      ...(files.find((f) => f.id === id)?.fetchedTags || {}),
                      ...tags,
                    },
                  }),
                );
                setModalState({ type: "none" });
                addToast("Zaktualizowano tagi", "success");
              }}
              files={selectedFiles}
            />
          )}
          {modalState.type === "preview-changes" && (
            <PreviewChangesModal
              isOpen={true}
              {...modalState}
              onCancel={() => setModalState({ type: "none" })}
            >
              {modalState.confirmationText}
            </PreviewChangesModal>
          )}
          {modalState.type === "post-download" && (
            <PostDownloadModal
              isOpen={true}
              onRemove={() => {
                removeFiles(selectedFileIds);
                setModalState({ type: "none" });
                addToast("Wyczyszczono kolejkę", "info");
              }}
              onKeep={() => setModalState({ type: "none" })}
              count={modalState.count}
            />
          )}
          {modalState.type === "rename" && (
            <RenameModal
              isOpen={true}
              onClose={() => setModalState({ type: "none" })}
              onSave={(pattern) => {
                setRenamePattern(pattern);
                setModalState({ type: "none" });
                addToast("Zapisano wzorzec nazw", "success");
              }}
              currentPattern={renamePattern}
              files={files}
            />
          )}
          {modalState.type === "duplicates" && (
            <DuplicateResolverModal
              isOpen={true}
              onClose={() => setModalState({ type: "none" })}
              duplicateSets={modalState.sets}
              onRemoveFiles={(ids) => {
                removeFiles(ids);
                setModalState({ type: "none" });
                addToast(`Rozwiązano duplikaty (${ids.length})`, "success");
              }}
            />
          )}
          {modalState.type === "xml-converter" && (
            <XmlConverterModal
              isOpen={true}
              onClose={() => setModalState({ type: "none" })}
            />
          )}
          {modalState.type === "smart-playlist" && (
            <SmartPlaylistModal
              isOpen={true}
              onClose={() => setModalState({ type: "none" })}
              files={files}
              onCreatePlaylist={(name, ids) => {
                createPlaylist(name, ids);
                setModalState({ type: "none" });
                addToast(`Utworzono playlistę AI: ${name}`, "success");
              }}
            />
          )}
          {modalState.type === "edit-tags" && (
            <EditTagsModal
              isOpen={true}
              onClose={() => setModalState({ type: "none" })}
              file={files.find(f => f.id === modalState.fileId)!}
              onSave={(tags) => {
                updateFile(modalState.fileId, { fetchedTags: tags });
                setModalState({ type: "none" });
                addToast("Zaktualizowano tagi", "success");
              }}
              onApply={async (tags) => {
                try {
                  const fileToUpdate = files.find(f => f.id === modalState.fileId);
                  if (fileToUpdate) {
                    await applyTags(fileToUpdate, tags, !!directoryHandle);
                    updateFile(modalState.fileId, { fetchedTags: tags, state: ProcessingState.SUCCESS });
                    setModalState({ type: "none" });
                    addToast("Zastosowano zmiany w pliku", "success");
                  }
                } catch (err: any) {
                  addToast(`Błąd zapisu: ${err.message}`, "error");
                }
              }}
              onManualSearch={async (q, f) => {
                // Trigger AI analysis with manual query
                await analyzeBatch([f], true);
              }}
              onZoomCover={() => {}}
              isApplying={false}
              isDirectAccessMode={!!directoryHandle}
              popularTags={popularTags}
            />
          )}
          {modalState.type === "smart-tagger" && (
            <SmartTaggerModal
              isOpen={true}
              onClose={() => setModalState({ type: "none" })}
              file={files.find((f) => f.id === modalState.fileId)!}
              onApply={(tags) => {
                updateFile(modalState.fileId, {
                  fetchedTags: tags,
                  state: ProcessingState.SUCCESS,
                });
                setModalState({ type: "none" });
                addToast("Zaktualizowano tagi (AI)", "success");
              }}
            />
          )}
        </>
      )}
    </div>
  );
};

export default App;
