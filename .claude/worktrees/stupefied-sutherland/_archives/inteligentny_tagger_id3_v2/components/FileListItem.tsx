import React, { useState } from 'react';
import { AudioFile } from '../types';
import { StatusIcon } from './StatusIcon';
import TagPreviewTooltip from './TagPreviewTooltip';
import { formatTime } from '../utils/formatUtils';

interface FileListItemProps {
  file: AudioFile;
  index: number;
  isSelected: boolean;
  onSelect: (file: AudioFile, e: React.MouseEvent) => void;
  onContextMenu: (file: AudioFile, e: React.MouseEvent) => void;
  onSelectionChange: (fileId: string, isSelected: boolean) => void;
  isPlaylistView: boolean;
  onReorder: (oldIndex: number, newIndex: number) => void;
}

const FileListItem: React.FC<FileListItemProps> = ({
  file,
  index,
  isSelected,
  onSelect,
  onContextMenu,
  onSelectionChange,
  isPlaylistView,
  onReorder,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const displayTags = file.fetchedTags || file.originalTags;
  const displayName = displayTags.title ? `${displayTags.artist || 'Brak artysty'} - ${displayTags.title}` : (file.newName || file.file.name);
  const displayBpm = displayTags.bpm ? Math.round(displayTags.bpm) : '-';
  const displayKey = displayTags.key || '-';
  const displayTime = file.duration ? formatTime(file.duration) : '-';

  const handleDragStart = (e: React.DragEvent<HTMLTableRowElement>) => {
    e.dataTransfer.setData('text/plain', JSON.stringify({
        source: isPlaylistView ? 'playlistReorder' : 'trackList',
        trackIds: [file.id], // Simplified to handle single or multiple later
        index: index,
    }));
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent<HTMLTableRowElement>) => {
    e.preventDefault();
    if (isPlaylistView) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };
  
  const handleDrop = (e: React.DragEvent<HTMLTableRowElement>) => {
    e.preventDefault();
    if (isPlaylistView) {
      const data = JSON.parse(e.dataTransfer.getData('text/plain'));
      if (data.source === 'playlistReorder') {
        onReorder(data.index, index);
      }
    }
    setIsDragOver(false);
  };

  return (
    <tr 
      onClick={(e) => onSelect(file, e)}
      onContextMenu={(e) => onContextMenu(file, e)}
      draggable={true}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`${file.isSelected ? 'selected' : ''} ${isDragOver ? 'bg-indigo-500/20' : ''}`}
      style={{ opacity: isDragOver ? 0.5 : 1 }}
    >
      <td>
        <input 
            type="checkbox"
            checked={!!file.isSelected}
            onChange={(e) => {
                e.stopPropagation();
                onSelectionChange(file.id, e.target.checked);
            }}
            onClick={(e) => e.stopPropagation()}
            className="h-4 w-4 rounded bg-slate-700 border-slate-600 text-accent-magenta focus:ring-accent-magenta"
        />
      </td>
      <td className="flex items-center gap-3">
        <div className="group relative">
            <StatusIcon state={file.state} errorMessage={file.errorMessage} />
            {file.state === 'SUCCESS' && <TagPreviewTooltip originalTags={file.originalTags} fetchedTags={file.fetchedTags} />}
        </div>
        <div className="truncate">
          <p className="font-bold text-sm text-text-dim truncate" title={displayName}>
              {displayName}
          </p>
           <p className="text-xs text-text-dark truncate" title={file.file.name}>
              {file.webkitRelativePath || file.file.name}
          </p>
        </div>
      </td>
      <td>{displayBpm}</td>
      <td>{displayKey}</td>
      <td>{displayTime}</td>
      <td>{new Date(file.dateAdded).toLocaleDateString()}</td>
      <td>{file.state}</td>
      <td>
       {/* Actions are now in context menu */}
      </td>
    </tr>
  );
};

export default FileListItem;