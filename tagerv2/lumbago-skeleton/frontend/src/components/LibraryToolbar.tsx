import React from "react";
import ThemeToggle from "./ThemeToggle";

interface LibraryToolbarProps {
  onImport: () => void;
  onSettings: () => void;
  onAnalyzeAll: () => void;
  onAnalyzeSelected: () => void;
  onForceAnalyzeSelected: () => void; // New prop for forced update
  onEdit: () => void;
  onExport: () => void;
  onDelete: () => void;
  onClearAll: () => void;
  onRename: () => void;
  onFindDuplicates: () => void;
  onExportCsv: () => void;

  selectedCount: number;
  totalCount: number;
  allSelected: boolean;
  onToggleSelectAll: () => void;

  theme: "light" | "dark";
  setTheme: (theme: "light" | "dark") => void;
  isProcessing: boolean;

  isDirectAccessMode: boolean;
  directoryName?: string;
  isRestored?: boolean;
}

const LibraryToolbar: React.FC<LibraryToolbarProps> = ({
  onImport,
  onSettings,
  onAnalyzeAll,
  onAnalyzeSelected,
  onForceAnalyzeSelected, // Destructure new prop
  onEdit,
  onExport,
  onDelete,
  onClearAll,
  onRename,
  onFindDuplicates,
  onExportCsv,

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
}) => {
  const hasSelection = selectedCount > 0;

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 flex-shrink-0 z-20">
      {/* Left: Search & Import */}
      <div className="flex items-center space-x-3 md:space-x-4">
        <button
          onClick={onImport}
          disabled={isProcessing}
          className="flex items-center px-3 md:px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-400 text-white text-sm font-bold rounded-md shadow-sm transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 mr-2"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
          <span className="hidden sm:inline">Importuj</span>
        </button>

        {isDirectAccessMode && (
          <div
            className="hidden lg:flex items-center text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded"
            title={`Pracujesz w folderze: ${directoryName}`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-3 w-3 mr-1"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm2 2v1h12V8H4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="truncate max-w-[150px]">{directoryName}</span>
          </div>
        )}
      </div>

      {/* Center: Actions */}
      <div className="flex items-center space-x-2 flex-grow justify-center mx-4">
        {hasSelection ? (
          <div className="flex items-center space-x-1 md:space-x-2 bg-indigo-50 dark:bg-indigo-900/20 px-2 md:px-3 py-1 rounded-md animate-fade-in border border-indigo-100 dark:border-indigo-900/30">
            <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-300 mr-2 whitespace-nowrap">
              {selectedCount}{" "}
              <span className="hidden sm:inline">zaznaczonych</span>
            </span>

            <button
              onClick={onAnalyzeSelected}
              disabled={isProcessing || isRestored}
              className="p-1.5 hover:bg-indigo-200 dark:hover:bg-indigo-800 rounded text-indigo-600 dark:text-indigo-300 transition-colors"
              title="Analizuj zaznaczone (Cache/AI)"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </button>
            <button
              onClick={onForceAnalyzeSelected}
              disabled={isProcessing || isRestored}
              className="hidden sm:inline-flex items-center px-2 py-1 ml-1 text-xs font-medium text-white bg-indigo-500 hover:bg-indigo-600 rounded transition-colors"
              title="Wymuś wyszukiwanie w sieci i aktualizację (pomiń cache)"
            >
              Aktualizuj (Web)
            </button>
            <button
              onClick={onEdit}
              disabled={isProcessing}
              className="p-1.5 hover:bg-indigo-200 dark:hover:bg-indigo-800 rounded text-indigo-600 dark:text-indigo-300 transition-colors"
              title="Edytuj zaznaczone"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
            </button>
            <button
              onClick={onExport}
              disabled={isProcessing || isRestored}
              className="p-1.5 hover:bg-indigo-200 dark:hover:bg-indigo-800 rounded text-indigo-600 dark:text-indigo-300 transition-colors"
              title={
                isDirectAccessMode ? "Zapisz zmiany" : "Pobierz zaznaczone"
              }
            >
              {isDirectAccessMode ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>
            <div className="w-px h-4 bg-indigo-200 dark:bg-indigo-800 mx-1"></div>
            <button
              onClick={onDelete}
              disabled={isProcessing}
              className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/50 rounded text-red-600 dark:text-red-400 transition-colors"
              title="Usuń zaznaczone"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
            <button
              onClick={onToggleSelectAll}
              className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-slate-500 dark:text-slate-400 transition-colors"
              title="Odznacz wszystko"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        ) : totalCount > 0 ? (
          <div className="flex items-center space-x-1 md:space-x-2 text-slate-600 dark:text-slate-300">
            <button
              onClick={onAnalyzeAll}
              disabled={isProcessing || isRestored}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors"
              title={
                isRestored
                  ? "Pliki wymagają ponownego załadowania"
                  : "Analizuj wszystko"
              }
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M5 4a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2V6a2 2 0 00-2-2H5zM5 16a2 2 0 00-2 2v.5a.5.5 0 00.5.5h13a.5.5 0 00.5-.5V18a2 2 0 00-2-2H5z" />
              </svg>
            </button>
            <button
              onClick={onFindDuplicates}
              disabled={isProcessing || totalCount < 2}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors"
              title="Znajdź duplikaty"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
              </svg>
            </button>
            <button
              onClick={onRename}
              disabled={isProcessing}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors"
              title="Wzór zmiany nazw"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
            </button>
            <button
              onClick={onExportCsv}
              disabled={isProcessing}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors"
              title="Eksportuj CSV"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
            <button
              onClick={onClearAll}
              disabled={isProcessing}
              className="p-2 hover:bg-red-100 dark:hover:bg-red-900/50 text-red-600 dark:text-red-400 rounded transition-colors"
              title={
                isDirectAccessMode ? "Zamknij folder" : "Wyczyść bibliotekę"
              }
            >
              {isDirectAccessMode ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </button>
          </div>
        ) : null}
      </div>

      {/* Right: Settings & Theme */}
      <div className="flex items-center space-x-2 md:space-x-3">
        <ThemeToggle theme={theme} setTheme={setTheme} />
        <button
          onClick={onSettings}
          className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
          title="Ustawienia"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </button>
      </div>
    </header>
  );
};

export default LibraryToolbar;
