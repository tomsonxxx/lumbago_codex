import React, { useCallback, useState, useRef } from 'react';

// Augment React's type definitions to include the non-standard 'webkitdirectory' 
// property for the input element, which allows selecting directories.
// Switched to global module augmentation to resolve module lookup issues.
declare global {
  namespace React {
    interface InputHTMLAttributes<T> {
      // FIX: Changed to camelCase to align with React's prop naming conventions for DOM attributes.
      webkitDirectory?: string;
    }
  }
}

interface FileDropzoneProps {
  onFilesSelected: (files: FileList) => void;
  onUrlSubmitted: (url: string) => Promise<void>;
  isProcessing: boolean;
}

const FileDropzone: React.FC<FileDropzoneProps> = ({ onFilesSelected, onUrlSubmitted, isProcessing }) => {
  const [isDragActive, setIsDragActive] = useState(false);
  const [url, setUrl] = useState('');
  const [isUrlProcessing, setIsUrlProcessing] = useState(false);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFilesSelected(e.dataTransfer.files);
    }
  }, [onFilesSelected]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFilesSelected(e.target.files);
      // Reset input value to allow selecting the same file(s) again
      e.target.value = '';
    }
  };
  
  const handleFolderButtonClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
      folderInputRef.current?.click();
  }
  
  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url || isProcessing || isUrlProcessing) return;

    setIsUrlProcessing(true);
    try {
      await onUrlSubmitted(url);
      setUrl(''); // Clear on success
    } catch (error) {
      // The parent component (App.tsx) will show an alert.
    } finally {
      setIsUrlProcessing(false);
    }
  };

  const activeClasses = isDragActive ? 'border-indigo-400 bg-slate-200 dark:bg-slate-700' : 'border-slate-400 dark:border-slate-600';

  return (
    <div
      className={`relative flex flex-col items-center justify-center w-full max-w-4xl p-8 mx-auto mt-8 border-2 border-dashed rounded-lg transition-colors duration-300 ${activeClasses} ${isProcessing ? 'cursor-not-allowed opacity-50' : ''}`}
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
        {...{ webkitdirectory: "" }}
        onChange={handleFileChange}
        disabled={isProcessing}
      />
      <label htmlFor="file-input" className="flex flex-col items-center justify-center text-center cursor-pointer">
        <svg xmlns="http://www.w3.org/2000/svg" className="w-16 h-16 mb-4 text-slate-500 dark:text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p className="text-xl font-semibold text-slate-700 dark:text-slate-300">Przeciągnij i upuść pliki audio tutaj</p>
        <p className="text-slate-600 dark:text-slate-500">lub kliknij, aby je wybrać</p>
      </label>
       <button 
         onClick={handleFolderButtonClick} 
         disabled={isProcessing}
         className="mt-4 px-4 py-2 text-sm font-semibold text-indigo-600 dark:text-indigo-300 bg-slate-200/50 dark:bg-slate-700/50 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-50 dark:focus:ring-offset-slate-900 focus:ring-indigo-500 z-10"
        >
            lub Wybierz cały folder
        </button>
      <p className="mt-4 text-xs text-slate-500 dark:text-slate-600">Obsługiwane formaty: MP3, FLAC, WAV, OGG, M4A, AAC, WMA</p>

        <div className="relative flex items-center w-full my-6">
            <div className="flex-grow border-t border-slate-300 dark:border-slate-700"></div>
            <span className="flex-shrink mx-4 text-slate-400 dark:text-slate-500 text-sm">LUB</span>
            <div className="flex-grow border-t border-slate-300 dark:border-slate-700"></div>
        </div>
        
        <form onSubmit={handleUrlSubmit} className="w-full z-10">
            <div className="flex items-center space-x-2">
                <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="Wklej adres URL do pliku audio..."
                    disabled={isProcessing || isUrlProcessing}
                    className="flex-grow bg-slate-100 dark:bg-slate-900/50 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm py-2 px-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:text-sm"
                    required
                />
                <button
                    type="submit"
                    disabled={isProcessing || isUrlProcessing || !url}
                    className="px-4 py-2 text-sm h-[40px] w-[140px] font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed flex items-center justify-center"
                >
                    {isUrlProcessing ? <span className="btn-spinner !mr-0"></span> : 'Przetwarzaj URL'}
                </button>
            </div>
        </form>

    </div>
  );
};

export default FileDropzone;