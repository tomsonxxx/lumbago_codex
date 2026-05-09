import React, { useCallback, useState, useRef } from "react";

// Fix: Augment React HTML props interface to include 'webkitdirectory'
declare module "react" {
  interface InputHTMLAttributes<T> extends React.HTMLAttributes<T> {
    webkitdirectory?: string;
  }
}

interface FileDropzoneProps {
  onFilesSelected: (files: FileList) => void;
  onUrlSubmitted: (url: string) => Promise<void>;
  isProcessing: boolean;
}

const FileDropzone: React.FC<FileDropzoneProps> = ({
  onFilesSelected,
  onUrlSubmitted,
  isProcessing,
}) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [url, setUrl] = useState("");
  const [isUrlProcessing, setIsUrlProcessing] = useState(false);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragActive(false);
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        onFilesSelected(e.dataTransfer.files);
      }
    },
    [onFilesSelected],
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(e.target.files);
      // Reset input value to allow selecting the same file(s) again
      e.target.value = "";
    }
  };

  const handleFolderButtonClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    folderInputRef.current?.click();
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url || isProcessing || isUrlProcessing) return;

    setIsUrlProcessing(true);
    try {
      await onUrlSubmitted(url);
      setUrl(""); // Clear on success
    } catch (error) {
      // The parent component (App.tsx) will show an alert.
    } finally {
      setIsUrlProcessing(false);
    }
  };

  const activeClasses = isDragActive
    ? "border-indigo-400 bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)]"
    : "border-[var(--border-color)] dark:border-[var(--border-color)]";

  return (
    <div
      className={`relative flex flex-col items-center justify-center w-full max-w-4xl p-8 mx-auto mt-8 border-2 border-dashed rounded-none transition-colors duration-300 ${activeClasses} ${isProcessing ? "cursor-not-allowed opacity-50" : ""}`}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id="file-input"
        className="absolute w-full h-full top-0 left-0 opacity-0 cursor-pointer"
        multiple
        accept="audio/mpeg, audio/mp3, audio/mp4, audio/flac, audio/wav, audio/ogg, audio/m4a, audio/x-m4a, audio/aac, audio/x-ms-wma"
        onChange={handleFileChange}
        disabled={isProcessing}
      />
      <input
        type="file"
        id="folder-input"
        ref={folderInputRef}
        className="hidden"
        multiple
        webkitdirectory=""
        onChange={handleFileChange}
        disabled={isProcessing}
      />
      <label
        htmlFor="file-input"
        className="flex flex-col items-center justify-center text-center cursor-pointer"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="w-16 h-16 mb-4 text-[var(--text-secondary)] dark:text-[var(--text-secondary)]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p className="text-xl font-semibold text-[var(--text-secondary)] dark:text-[var(--text-secondary)]">
          Przeciągnij i upuść pliki audio tutaj
        </p>
        <p className="text-[var(--text-secondary)] dark:text-[var(--text-secondary)]">
          lub kliknij, aby je wybrać
        </p>
      </label>
      <button
        onClick={handleFolderButtonClick}
        disabled={isProcessing}
        className="mt-4 px-4 py-2 text-sm font-semibold text-[var(--accent-primary)] dark:text-[var(--accent-primary)] bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] rounded-none hover:bg-[var(--bg-panel)] dark:hover:bg-[var(--bg-panel)] transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-50 dark:focus:ring-offset-slate-900 focus:ring-[var(--accent-primary)] z-10"
      >
        lub Wybierz cały folder
      </button>
      <p className="mt-4 text-xs text-[var(--text-secondary)] dark:text-[var(--text-secondary)]">
        Obsługiwane formaty: MP3, FLAC, WAV, OGG, M4A, AAC, WMA
      </p>

      <div className="relative flex items-center w-full my-6">
        <div className="flex-grow border-t border-[var(--border-color)] dark:border-[var(--border-color)]"></div>
        <span className="flex-shrink mx-4 text-[var(--text-secondary)] dark:text-[var(--text-secondary)] text-sm">
          LUB
        </span>
        <div className="flex-grow border-t border-[var(--border-color)] dark:border-[var(--border-color)]"></div>
      </div>

      <form onSubmit={handleUrlSubmit} className="w-full z-10">
        <div className="flex items-center space-x-2">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Wklej adres URL do pliku audio..."
            disabled={isProcessing || isUrlProcessing}
            className="flex-grow bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] border border-[var(--border-color)] dark:border-[var(--border-color)] rounded-none shadow-sm py-2 px-3 text-[var(--text-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] sm:text-sm"
            required
          />
          <button
            type="submit"
            disabled={isProcessing || isUrlProcessing || !url}
            className="px-4 py-2 text-sm h-[40px] w-[140px] font-bold text-white bg-[var(--accent-secondary)] rounded-none hover:bg-[var(--accent-secondary)] disabled:bg-[var(--accent-secondary)] disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isUrlProcessing ? (
              <span className="btn-spinner !mr-0"></span>
            ) : (
              "Przetwarzaj URL"
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileDropzone;
