
import React, { useEffect, useRef, useState, Suspense } from 'react';
import { AudioFile, ProcessingState } from '../types';
import { StatusIcon } from './StatusIcon';
import AlbumCover from './AlbumCover';
import MiniAudioVisualizer from './MiniAudioVisualizer';

const TagPreviewTooltip = React.lazy(() => import('./TagPreviewTooltip'));

interface FileListItemProps {
  file: AudioFile;
  onEdit: (file: AudioFile) => void;
  onProcess: (file: AudioFile) => void;
  onDelete: (fileId: string) => void;
  onSelectionChange: (fileId: string, isSelected: boolean) => void;
  // Player Props
  isPlaying?: boolean;
  onPlayPause?: () => void;
  isActive?: boolean;
  // Inspect Prop
  onInspect: () => void;
  // Playlist & Favs
  onToggleFavorite: (fileId: string) => void;
  onAddToPlaylist: (fileId: string) => void;
  // Layout Prop
  gridClass?: string; 
}

const FileListItem: React.FC<FileListItemProps> = ({
  file,
  onEdit,
  onProcess,
  onDelete,
  onSelectionChange,
  isPlaying,
  onPlayPause,
  isActive,
  onInspect,
  onToggleFavorite,
  onAddToPlaylist,
  gridClass
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const hoverTimeoutRef = useRef<any>(null);

  const isProcessing = file.state === ProcessingState.PROCESSING || file.state === ProcessingState.DOWNLOADING;
  const hasFetchedTags = file.fetchedTags && Object.keys(file.fetchedTags).length > 0;
  
  const displayTags = file.fetchedTags || file.originalTags;
  const displayName = file.newName || file.file.name;

  const handleMouseEnter = () => {
      if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
      if (hasFetchedTags) {
          hoverTimeoutRef.current = setTimeout(() => {
              setIsHovered(true);
          }, 300);
      }
  };

  const handleMouseLeave = () => {
      if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
      setIsHovered(false);
  };

  let rowClasses = "relative group transition-all duration-200 rounded-lg hover:bg-white/5 border border-transparent ";
  
  if (isActive) {
      rowClasses += "bg-indigo-500/10 border-indigo-500/30 ";
  } else if (file.isSelected) {
      rowClasses += "bg-cyan-900/20 border-cyan-500/30 ";
  } else {
      rowClasses += "border-slate-800/50 ";
  }

  // Common text styles
  const cellText = "truncate text-xs text-slate-400 group-hover:text-slate-200 transition-colors font-medium";

  return (
    <div className={`${rowClasses} ${gridClass ? `${gridClass} items-center py-2 px-2` : "flex items-center p-2"}`}>
      
      {/* --- Checkbox Column --- */}
      <div className={`flex items-center justify-center`}>
          <input 
            type="checkbox"
            checked={!!file.isSelected}
            onChange={(e) => { e.stopPropagation(); onSelectionChange(file.id, e.target.checked); }}
            className="h-4 w-4 rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-offset-0 focus:ring-0 cursor-pointer"
          />
      </div>

      {/* --- Title & Cover Column --- */}
      <div className={`flex items-center gap-3 overflow-hidden ${!gridClass ? 'flex-grow ml-2' : ''}`}>
          
          <div className="relative group/cover flex-shrink-0" onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
             <div className="relative w-9 h-9">
                <AlbumCover tags={displayTags} className="w-full h-full rounded-md shadow-lg" />
                <button 
                    onClick={(e) => { e.stopPropagation(); onPlayPause && onPlayPause(); }}
                    className={`absolute inset-0 flex items-center justify-center bg-black/50 rounded-md transition-opacity ${isActive || isPlaying ? 'opacity-100' : 'opacity-0 group-hover/cover:opacity-100'}`}
                >
                    {isPlaying ? (
                        <div className="flex space-x-[2px] items-end h-3">
                             <div className="w-[2px] h-3 bg-cyan-400 animate-[music-bar_0.6s_ease-in-out_infinite]"></div>
                             <div className="w-[2px] h-3 bg-cyan-400 animate-[music-bar_0.8s_ease-in-out_infinite]"></div>
                             <div className="w-[2px] h-3 bg-cyan-400 animate-[music-bar_0.5s_ease-in-out_infinite]"></div>
                        </div>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white pl-0.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                    )}
                </button>
             </div>
             {hasFetchedTags && isHovered && (
                <Suspense fallback={null}>
                    <TagPreviewTooltip originalTags={file.originalTags} fetchedTags={file.fetchedTags} />
                </Suspense>
            )}
          </div>

          <div className="min-w-0 flex flex-col justify-center">
             <div className="flex items-center gap-2">
                <span className={`font-bold text-sm truncate cursor-pointer ${isActive ? 'text-cyan-400 neon-text-blue' : 'text-slate-200 group-hover:text-white'}`} title={displayName}>
                    {displayName}
                </span>
             </div>
             
             {/* Status / Subtitle */}
             <div className="flex items-center h-4">
                 {file.state === ProcessingState.ERROR ? (
                    <span className="text-[10px] text-red-500 truncate">{file.errorMessage || 'Błąd'}</span>
                 ) : isProcessing ? (
                    <div className="w-16 h-1 bg-slate-800 rounded overflow-hidden">
                        <div className="h-full bg-cyan-500 animate-indeterminate-bar"></div>
                    </div>
                 ) : (
                    <div className="flex items-center gap-2">
                        {file.isFavorite && <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-red-500" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" /></svg>}
                        <StatusIcon state={file.state} />
                    </div>
                 )}
             </div>
          </div>
      </div>

      {/* --- Artist Column (Desktop) --- */}
      <div className={`hidden md:block ${cellText}`} title={displayTags?.artist}>
          {displayTags?.artist || '-'}
      </div>

      {/* --- Album Column (Desktop) --- */}
      <div className={`hidden md:block ${cellText}`} title={displayTags?.album}>
          {displayTags?.album || '-'}
      </div>

      {/* --- BPM Column (Desktop) --- */}
      <div className="hidden md:block truncate text-xs font-mono text-cyan-600 group-hover:text-cyan-400 transition-colors font-bold">
          {displayTags?.bpm || '-'}
      </div>

      {/* --- Key Column (Desktop) --- */}
      <div className="hidden md:block truncate text-xs font-mono text-fuchsia-600 group-hover:text-fuchsia-400 transition-colors font-bold">
          {displayTags?.initialKey || '-'}
      </div>

    </div>
  );
};

export default FileListItem;
