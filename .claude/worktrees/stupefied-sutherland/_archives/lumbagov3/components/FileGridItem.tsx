

import React from 'react';
import { AudioFile, ProcessingState } from '../types';
import AlbumCover from './AlbumCover';
import { StatusIcon } from './StatusIcon';

interface FileGridItemProps {
  file: AudioFile;
  onEdit: (file: AudioFile) => void;
  onProcess: (file: AudioFile) => void;
  onSelectionChange: (fileId: string, isSelected: boolean) => void;
  // Player Props
  isPlaying?: boolean;
  onPlayPause?: () => void;
  isActive?: boolean;
  // Inspect Prop
  onInspect: () => void;
}

const FileGridItem: React.FC<FileGridItemProps> = ({
  file,
  onEdit,
  onProcess,
  onSelectionChange,
  isPlaying,
  onPlayPause,
  isActive,
  onInspect
}) => {
  const isProcessing = file.state === ProcessingState.PROCESSING || file.state === ProcessingState.DOWNLOADING;
  const hasBeenProcessed = file.state === ProcessingState.SUCCESS || file.state === ProcessingState.ERROR;
  
  const displayTags = file.fetchedTags || file.originalTags;
  const displayName = file.newName || file.file.name;
  
  let containerClasses = "relative group bg-white dark:bg-slate-800 rounded-xl shadow-sm hover:shadow-md border border-slate-200 dark:border-slate-700 overflow-hidden transition-all duration-300 flex flex-col";
  
  if (file.isSelected) {
      containerClasses += " ring-2 ring-indigo-500 border-indigo-500";
  } else if (isActive) {
      containerClasses += " ring-2 ring-indigo-400 border-indigo-400 dark:ring-indigo-600 dark:border-indigo-600";
  }
  
  if (isProcessing) {
      containerClasses += " animate-pulse border-indigo-300 dark:border-indigo-700";
  }

  return (
    <div className={containerClasses}>
      {/* Sekcja Okładki */}
      <div className="relative aspect-square w-full bg-slate-100 dark:bg-slate-900 overflow-hidden cursor-pointer" onClick={() => onSelectionChange(file.id, !file.isSelected)}>
         <AlbumCover tags={displayTags} className="w-full h-full object-cover" />
         
         {/* Overlay statusu */}
         <div className={`absolute top-0 right-0 p-2 z-10 transition-opacity ${file.isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
             <div className="bg-white/90 dark:bg-slate-900/90 rounded-full p-1 shadow-sm backdrop-blur-sm mb-2">
                 <input 
                    type="checkbox"
                    checked={!!file.isSelected}
                    onChange={(e) => { e.stopPropagation(); onSelectionChange(file.id, e.target.checked); }}
                    className="h-4 w-4 rounded bg-transparent border-none text-indigo-500 focus:ring-0 cursor-pointer"
                 />
             </div>
             <div className="bg-white/90 dark:bg-slate-900/90 rounded-full p-1 shadow-sm backdrop-blur-sm">
                 <StatusIcon state={file.state} />
             </div>
         </div>

         {/* Central Play/Pause Overlay */}
         <div className={`absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[1px] transition-opacity ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
            <button
                onClick={(e) => { e.stopPropagation(); onPlayPause && onPlayPause(); }}
                className="w-12 h-12 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-md flex items-center justify-center text-white transition-transform transform hover:scale-110"
            >
                {isPlaying ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 pl-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                )}
            </button>
         </div>

         {/* Przyciski akcji (Dół okładki) */}
         <div className="absolute bottom-0 inset-x-0 p-2 flex justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity translate-y-2 group-hover:translate-y-0 duration-200">
            {!hasBeenProcessed && !isProcessing && (
                <button 
                    onClick={(e) => { e.stopPropagation(); onProcess(file); }}
                    className="p-1.5 bg-indigo-600 text-white rounded-full hover:bg-indigo-500 shadow-lg"
                    title="Przetwarzaj"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
                </button>
            )}
             <button 
                onClick={(e) => { e.stopPropagation(); onInspect(); }}
                className="p-1.5 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-600 shadow-lg border border-slate-200 dark:border-slate-600"
                title="Szczegóły"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>
            </button>
            <button 
                onClick={(e) => { e.stopPropagation(); onEdit(file); }}
                className="p-1.5 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-600 shadow-lg border border-slate-200 dark:border-slate-600"
                title="Edytuj"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
            </button>
         </div>
      </div>

      <div className="p-3 flex flex-col justify-between flex-grow">
          <div>
            <h4 className={`font-bold text-sm truncate transition-colors ${isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-900 dark:text-white'}`} title={displayName}>
                {displayName}
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                {displayTags?.artist || 'Nieznany Artysta'}
            </p>
          </div>
          
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-100 dark:border-slate-700/50">
             <div className="flex gap-1">
                 {displayTags?.year && (
                     <span className="text-[10px] bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 px-1.5 py-0.5 rounded">
                         {displayTags.year}
                     </span>
                 )}
                 {displayTags?.genre && (
                     <span className="text-[10px] bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-1.5 py-0.5 rounded truncate max-w-[60px]">
                         {displayTags.genre}
                     </span>
                 )}
             </div>
          </div>
      </div>
      
      {file.state === ProcessingState.ERROR && (
          <div className="absolute bottom-0 left-0 right-0 bg-red-500 text-white text-[10px] px-2 py-1 truncate" title={file.errorMessage}>
              Błąd: {file.errorMessage}
          </div>
      )}
    </div>
  );
};

export default FileGridItem;