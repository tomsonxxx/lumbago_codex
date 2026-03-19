
import React from 'react';
import { AudioFile } from '../types';
import AlbumCover from './AlbumCover';
import { StatusIcon } from './StatusIcon';

interface TrackGridProps {
  files: AudioFile[];
  selectedFileIds: string[];
  activeFileId: string | null;
  onSelect: (id: string, multi: boolean) => void;
  onActivate: (file: AudioFile) => void;
}

const TrackGrid: React.FC<TrackGridProps> = ({
  files,
  selectedFileIds,
  activeFileId,
  onSelect,
  onActivate,
}) => {
  if (files.length === 0) return null;

  return (
    <div className="flex-grow overflow-y-auto bg-slate-50 dark:bg-slate-900 p-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-4">
        {files.map((file) => {
          const isSelected = selectedFileIds.includes(file.id);
          const isActive = activeFileId === file.id;
          const tags = file.fetchedTags || file.originalTags || {};
          const title = tags.title || file.file.name;
          const artist = tags.artist || 'Nieznany';

          return (
            <div
              key={file.id}
              onClick={(e) => onSelect(file.id, e.ctrlKey || e.metaKey || e.shiftKey)}
              onDoubleClick={() => onActivate(file)}
              className={`
                group relative bg-white dark:bg-slate-800 rounded-lg shadow-sm border transition-all duration-200 cursor-pointer overflow-hidden flex flex-col animate-fade-in
                ${isSelected ? 'ring-2 ring-indigo-500 border-transparent' : 'border-slate-200 dark:border-slate-700 hover:shadow-md hover:border-slate-300 dark:hover:border-slate-600'}
                ${isActive ? 'ring-2 ring-indigo-500 bg-indigo-50 dark:bg-slate-700' : ''}
              `}
            >
              {/* Cover Art Area */}
              <div className="aspect-square w-full relative bg-slate-200 dark:bg-slate-900">
                <AlbumCover tags={tags} className="w-full h-full rounded-t-lg" />
                
                {/* Overlay Status Icon */}
                <div className="absolute top-2 right-2 p-1 bg-white/80 dark:bg-black/50 rounded-full shadow-sm backdrop-blur-sm">
                   <div className="scale-75 origin-center">
                     <StatusIcon state={file.state} />
                   </div>
                </div>

                {/* Selection Checkbox (visible on hover or selected) */}
                <div className={`absolute top-2 left-2 ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} transition-opacity`}>
                   <input 
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}} // Handled by parent div click usually, but keeping strictly visual here
                      className="h-5 w-5 rounded bg-slate-100 dark:bg-slate-700 border-slate-300 dark:border-slate-500 text-indigo-600 focus:ring-indigo-500 cursor-pointer shadow-sm"
                   />
                </div>

                {/* Play Button Overlay */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/20">
                    <button 
                        onClick={(e) => { e.stopPropagation(); onActivate(file); }}
                        className="w-12 h-12 bg-indigo-600/90 hover:bg-indigo-500 text-white rounded-full flex items-center justify-center shadow-lg transform hover:scale-105 transition-all"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 pl-1" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                        </svg>
                    </button>
                </div>
              </div>

              {/* Metadata Area */}
              <div className="p-3 flex flex-col flex-grow">
                <h3 className="font-bold text-sm text-slate-900 dark:text-white truncate" title={title}>
                  {title}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5" title={artist}>
                  {artist}
                </p>
                
                <div className="mt-auto pt-2 flex items-center justify-between text-[10px] text-slate-400 dark:text-slate-500 font-mono uppercase">
                    <span className="truncate">{tags.bpm ? `${tags.bpm} BPM` : ''}</span>
                    <span className="truncate ml-2">{tags.initialKey || ''}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TrackGrid;
