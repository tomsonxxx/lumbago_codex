
import React, { useEffect, useRef, useState } from 'react';
import { AudioFile, ProcessingState } from '../types';
import { StatusIcon } from './StatusIcon';
import AlbumCover from './AlbumCover';
import TagPreviewTooltip from './TagPreviewTooltip';
import { isTagWritingSupported } from '../utils/audioUtils';

interface FileListItemProps {
  file: AudioFile;
  onEdit: (file: AudioFile) => void;
  onProcess: (file: AudioFile) => void;
  onDelete: (fileId: string) => void;
  onSelectionChange: (fileId: string, isSelected: boolean) => void;
}

function usePrevious<T>(value: T): T | undefined {
    const ref = useRef<T | undefined>(undefined);
    useEffect(() => {
        ref.current = value;
    });
    return ref.current;
}

const FileListItem: React.FC<FileListItemProps> = ({
  file,
  onEdit,
  onProcess,
  onDelete,
  onSelectionChange,
}) => {
  const [isExiting, setIsExiting] = useState(false);
  const itemRef = useRef<HTMLDivElement>(null);
  const prevState = usePrevious(file.state);

  const isProcessing = file.state === ProcessingState.PROCESSING || file.state === ProcessingState.DOWNLOADING;
  const hasBeenProcessed = file.state === ProcessingState.SUCCESS || file.state === ProcessingState.ERROR;
  const hasFetchedTags = file.fetchedTags && Object.keys(file.fetchedTags).length > 0;
  
  const displayTags = file.fetchedTags || file.originalTags;
  const displayName = file.newName || file.file.name;
  const hasNewName = !!file.newName && file.newName !== file.file.name;
  const supportsTagWriting = isTagWritingSupported(file.file);
  
  // Confidence Indicator Logic
  const confidence = file.fetchedTags?.confidence;
  let confidenceColor = 'bg-slate-300'; // none
  if (confidence === 'high') confidenceColor = 'bg-green-500';
  if (confidence === 'medium') confidenceColor = 'bg-yellow-500';
  if (confidence === 'low') confidenceColor = 'bg-red-500';

  useEffect(() => {
    const element = itemRef.current;
    if (!element) return;
    
    // Animate status change flash
    if (prevState === ProcessingState.PROCESSING) {
      if (file.state === ProcessingState.SUCCESS) {
        element.classList.add('animate-flash-success');
      } else if (file.state === ProcessingState.ERROR) {
        element.classList.add('animate-flash-error');
      }
       // Clean up animation class
       element.addEventListener('animationend', () => {
            element.classList.remove('animate-flash-success', 'animate-flash-error');
       }, { once: true });
    }
  }, [file.state, prevState]);
  
  const handleDelete = () => {
    setIsExiting(true);
    setTimeout(() => {
        onDelete(file.id);
    }, 300);
  };

  const itemClasses = [
      "flex items-center p-3 bg-white dark:bg-slate-800 rounded-lg shadow-sm transition-all duration-300 border",
      file.isSelected ? 'border-indigo-500 ring-2 ring-indigo-500/50' : 'border-transparent dark:border-slate-700',
      file.duplicateSetId ? 'bg-amber-50 dark:bg-amber-900/20' : '',
      isExiting ? 'animate-fade-out' : 'animate-fade-in'
  ].join(' ');

  return (
    <div ref={itemRef} className={itemClasses}>
      <input 
        type="checkbox"
        checked={!!file.isSelected}
        onChange={(e) => onSelectionChange(file.id, e.target.checked)}
        className="h-5 w-5 rounded bg-slate-200 dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500 mr-4 flex-shrink-0"
      />
      <StatusIcon state={file.state} />
      <div className="relative group">
        <AlbumCover tags={displayTags} />
        {hasFetchedTags && <TagPreviewTooltip originalTags={file.originalTags} fetchedTags={file.fetchedTags} />}
        
        {/* Confidence Badge */}
        {hasFetchedTags && confidence && (
            <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border border-white ${confidenceColor}`} title={`AI Confidence: ${confidence}`} />
        )}
      </div>
      <div className="flex-grow ml-4 overflow-hidden">
        <div className="flex items-center gap-2">
            {file.duplicateSetId && (
                <div className="flex-shrink-0" title="Potencjalny duplikat">
                     <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                        Dup
                     </span>
                </div>
            )}
            <p className="font-bold text-sm text-slate-800 dark:text-slate-200 truncate" title={displayName}>
                {displayName}
            </p>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 truncate" title={file.file.name}>
          {hasNewName ? `Oryginalnie: ${file.file.name}` : `Artysta: ${displayTags?.artist || 'Brak'}`}
        </p>
         {!supportsTagWriting && hasBeenProcessed && file.state !== ProcessingState.ERROR && (
            <p className="text-xs text-amber-600 dark:text-amber-500 mt-1 truncate">
                Tylko zmiana nazwy (Format nieobsługiwany)
            </p>
        )}
        {file.state === ProcessingState.ERROR && (
          <p className="text-xs text-red-500 dark:text-red-400 mt-1 truncate" title={file.errorMessage}>
            {file.errorMessage}
          </p>
        )}
      </div>
      <div className="flex items-center space-x-2 ml-4 flex-shrink-0">
        {!hasBeenProcessed && (
           <button onClick={() => onProcess(file)} disabled={isProcessing} className="p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 disabled:opacity-50 disabled:cursor-not-allowed" title="Przetwarzaj">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
           </button>
        )}
         <button onClick={() => onEdit(file)} className="p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400" title="Edytuj tagi">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
         </button>
         <button onClick={handleDelete} className="p-2 rounded-md hover:bg-red-100 dark:hover:bg-red-900/50 text-red-500 dark:text-red-400" title="Usuń">
           <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
         </button>
      </div>
    </div>
  );
};

export default FileListItem;
