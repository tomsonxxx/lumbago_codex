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
  onRetry: (fileId: string) => void;
}

const usePrevious = <T,>(value: T): T | undefined => {
  const ref = useRef<T | undefined>(undefined);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
};

const FileListItem: React.FC<FileListItemProps> = ({ file, onEdit, onProcess, onDelete, onSelectionChange, onRetry }) => {
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

  useEffect(() => {
    const element = itemRef.current;
    if (!element) return;
    if (prevState === ProcessingState.PROCESSING) {
      if (file.state === ProcessingState.SUCCESS) {
        element.classList.add('animate-flash-success');
      } else if (file.state === ProcessingState.ERROR) {
        element.classList.add('animate-flash-error');
      }
      element.addEventListener(
        'animationend',
        () => {
          element.classList.remove('animate-flash-success', 'animate-flash-error');
        },
        { once: true }
      );
    }
  }, [file.state, prevState]);

  const handleDelete = () => {
    setIsExiting(true);
    setTimeout(() => onDelete(file.id), 300);
  };

  let bgClass = 'bg-white dark:bg-slate-800';
  let borderClass = 'border-transparent dark:border-slate-700';

  if (isProcessing) {
    bgClass =
      'bg-gradient-to-r from-slate-50 via-indigo-50 to-slate-50 dark:from-slate-800 dark:via-indigo-900/20 dark:to-slate-800 animate-gradient-loading';
    borderClass = 'border-indigo-200 dark:border-indigo-900';
  }
  if (file.isSelected) {
    borderClass = 'border-indigo-500 ring-2 ring-indigo-500/50';
  }

  const itemClasses = [
    'flex items-center p-3 rounded-lg shadow-sm transition-all duration-300 border',
    bgClass,
    borderClass,
    file.state === ProcessingState.SUCCESS ? 'opacity-70' : '',
    isExiting ? 'animate-fade-out' : 'animate-fade-in',
  ].join(' ');

  return (
    <div ref={itemRef} className={itemClasses}>
      <input
        type="checkbox"
        checked={!!file.isSelected}
        onChange={(event) => onSelectionChange(file.id, event.target.checked)}
        className="h-5 w-5 rounded bg-slate-200 text-indigo-600 mr-4 flex-shrink-0"
      />
      <StatusIcon state={file.state} />
      <div className="relative group">
        <AlbumCover tags={displayTags} />
        {hasFetchedTags && <TagPreviewTooltip originalTags={file.originalTags} fetchedTags={file.fetchedTags} />}
      </div>
      <div className="flex-grow ml-4 overflow-hidden">
        <p className="font-bold text-sm text-slate-800 dark:text-slate-200 truncate" title={displayName}>
          {displayName}
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400 truncate" title={file.file.name}>
          {hasNewName ? `Original: ${file.file.name}` : `Artist: ${displayTags?.artist || 'Brak'}`}
        </p>
        {!supportsTagWriting && hasBeenProcessed && file.state !== ProcessingState.ERROR && (
          <p className="text-xs text-amber-600 dark:text-amber-500 mt-1 truncate">Only rename supported for this format.</p>
        )}
        {file.state === ProcessingState.ERROR && (
          <p className="text-xs text-fuchsia-600 dark:text-fuchsia-400 mt-1 truncate" title={file.errorMessage}>
            {file.errorMessage}
          </p>
        )}
      </div>

      <div className="hidden md:flex items-center w-20 ml-4 justify-center">
        <span className="text-xs font-mono bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded text-slate-600 dark:text-slate-300">
          {displayTags?.bpm || 120}
        </span>
      </div>
      <div className="hidden md:flex items-center w-20 ml-4 justify-center">
        <span className="text-xs font-mono bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded text-slate-600 dark:text-slate-300">
          {displayTags?.key || 'C min'}
        </span>
      </div>

      <div className="flex items-center space-x-2 ml-4 flex-shrink-0 w-40 justify-end">
        {!hasBeenProcessed && (
          <button
            onClick={() => onProcess(file)}
            disabled={isProcessing}
            className="p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 disabled:opacity-50"
            title="Process"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
        <button onClick={() => onEdit(file)} className="p-2 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400" title="Edit tags">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
        </button>
        <button onClick={handleDelete} className="p-2 rounded-md hover:bg-red-100 dark:hover:bg-red-900/50 text-red-500 dark:text-red-400" title="Delete">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </button>
        {file.state === ProcessingState.ERROR && (
          <button
            onClick={() => onRetry(file.id)}
            className="p-2 rounded-md hover:bg-fuchsia-100 dark:hover:bg-fuchsia-900/40 text-fuchsia-500 dark:text-fuchsia-300"
            title="Retry"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M15.312 11.424a5 5 0 01-9.017 1.219 1 1 0 00-1.732 1 7 7 0 0012.622-1.714H18a1 1 0 100-2h-3.5a1 1 0 00-.98.804z"
                clipRule="evenodd"
              />
              <path
                fillRule="evenodd"
                d="M4.688 8.576a5 5 0 019.017-1.219 1 1 0 001.732-1A7 7 0 002.815 8H2a1 1 0 100 2h3.5a1 1 0 00.98-.804z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default FileListItem;

