
import React from 'react';
import { AudioFile, ProcessingState } from '../types';
import AlbumCover from './AlbumCover';
import { StatusIcon } from './StatusIcon';

interface FileGridItemProps {
  file: AudioFile;
  onEdit: (file: AudioFile) => void;
  onProcess: (file: AudioFile) => void;
  onSelectionChange: (fileId: string, isSelected: boolean) => void;
}

const FileGridItem: React.FC<FileGridItemProps> = ({
  file,
  onEdit,
  onProcess,
  onSelectionChange,
}) => {
  const isProcessing = file.state === ProcessingState.PROCESSING || file.state === ProcessingState.DOWNLOADING;
  const hasBeenProcessed = file.state === ProcessingState.SUCCESS || file.state === ProcessingState.ERROR;
  
  const displayTags = file.fetchedTags || file.originalTags;
  const displayName = file.newName || file.file.name;
  
  // Dynamiczne klasy dla stanów
  let containerClasses = "relative group bg-white dark:bg-slate-800 rounded-xl shadow-sm hover:shadow-md border border-slate-200 dark:border-slate-700 overflow-hidden transition-all duration-300 flex flex-col";
  
  if (file.isSelected) {
      containerClasses += " ring-2 ring-indigo-500 border-indigo-500";
  }
  
  if (isProcessing) {
      containerClasses += " animate-pulse border-indigo-300 dark:border-indigo-700";
  }

  return (
    <div className={containerClasses}>
      {/* Sekcja Okładki */}
      <div className="relative aspect-square w-full bg-slate-100 dark:bg-slate-900 overflow-hidden cursor-pointer" onClick={() => onSelectionChange(file.id, !file.isSelected)}>
         <AlbumCover tags={displayTags} className="w-full h-full object-cover" />
         
         {/* Overlay przy hover lub zaznaczeniu */}
         <div className={`absolute inset-0 bg-black/40 transition-opacity flex items-start justify-between p-2 ${file.isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
             <input 
                type="checkbox"
                checked={!!file.isSelected}
                onChange={(e) => { e.stopPropagation(); onSelectionChange(file.id, e.target.checked); }}
                className="h-5 w-5 rounded bg-white/20 border-white/50 text-indigo-500 focus:ring-indigo-500 cursor-pointer backdrop-blur-sm"
             />
             <div className="bg-white/90 dark:bg-slate-900/90 rounded-full p-1 shadow-sm backdrop-blur-sm">
                 <StatusIcon state={file.state} />
             </div>
         </div>

         {/* Przycisk akcji na środku (Process/Edit) */}
         <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
             <div className="flex space-x-2 pointer-events-auto transform translate-y-4 group-hover:translate-y-0 transition-transform duration-200">
                {!hasBeenProcessed && !isProcessing && (
                    <button 
                        onClick={(e) => { e.stopPropagation(); onProcess(file); }}
                        className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-500 shadow-lg"
                        title="Przetwarzaj"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
                    </button>
                )}
                <button 
                    onClick={(e) => { e.stopPropagation(); onEdit(file); }}
                    className="p-2 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-600 shadow-lg border border-slate-200 dark:border-slate-600"
                    title="Edytuj"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
                </button>
             </div>
         </div>
      </div>

      {/* Sekcja Metadanych */}
      <div className="p-3 flex flex-col justify-between flex-grow">
          <div>
            <h4 className="font-bold text-sm text-slate-900 dark:text-white truncate" title={displayName}>
                {displayName}
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                {displayTags?.artist || 'Nieznany Artysta'}
            </p>
            <p className="text-xs text-slate-400 dark:text-slate-500 truncate mt-0.5">
                {displayTags?.album || 'Nieznany Album'}
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
                 <span className="text-[10px] bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.5 rounded">
                     {displayTags?.bpm || 120} BPM
                 </span>
                 <span className="text-[10px] bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 px-1.5 py-0.5 rounded">
                     {displayTags?.key || 'C min'}
                 </span>
             </div>
          </div>
      </div>
      
      {/* Pasek statusu błędu */}
      {file.state === ProcessingState.ERROR && (
          <div className="absolute bottom-0 left-0 right-0 bg-red-500 text-white text-[10px] px-2 py-1 truncate" title={file.errorMessage}>
              Błąd: {file.errorMessage}
          </div>
      )}
    </div>
  );
};

export default FileGridItem;
