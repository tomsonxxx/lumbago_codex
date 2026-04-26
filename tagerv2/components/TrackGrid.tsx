import React from "react";
import { AudioFile } from "../types";
import AlbumCover from "./AlbumCover";
import { StatusIcon } from "./StatusIcon";

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
    <div className="flex-grow overflow-y-auto bg-[var(--bg-base)] p-4 scrollbar-thin">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-4">
        {files.map((file) => {
          const isSelected = selectedFileIds.includes(file.id);
          const isActive = activeFileId === file.id;
          const tags = file.fetchedTags || file.originalTags || {};
          const title = tags.title || file.file.name;
          const artist = tags.artist || "Unknown";

          return (
            <div
              key={file.id}
              onClick={(e) =>
                onSelect(file.id, e.ctrlKey || e.metaKey || e.shiftKey)
              }
              onDoubleClick={() => onActivate(file)}
              className={`
                group relative bg-[var(--bg-surface)] border transition-all duration-200 cursor-pointer overflow-hidden flex flex-col
                ${isSelected ? "border-[var(--accent-primary)] ring-1 ring-[var(--accent-primary)]" : "border-[var(--border-color)] hover:border-[#666]"}
                ${isActive ? "bg-[#222]" : ""}
              `}
            >
              {/* Cover Art Area */}
              <div className="aspect-square w-full relative bg-[var(--bg-panel)]">
                <AlbumCover tags={tags} className="w-full h-full" />

                {/* Overlay Status Icon */}
                <div className="absolute top-2 right-2 p-1 bg-black/80 rounded-none border border-[var(--border-color)]">
                  <div className="scale-75 origin-center">
                    <StatusIcon state={file.state} />
                  </div>
                </div>

                {/* Selection Checkbox */}
                <div
                  className={`absolute top-2 left-2 ${isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100"} transition-opacity`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}} // Handled by parent div click usually, but keeping strictly visual here
                    className="h-4 w-4 rounded-none bg-[var(--bg-panel)] border-[var(--border-color)] checked:bg-[var(--accent-primary)] checked:border-[var(--accent-primary)] focus:ring-1 focus:ring-[var(--accent-primary)] focus:ring-offset-0 focus:ring-offset-transparent cursor-pointer"
                  />
                </div>

                {/* Play Button Overlay */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onActivate(file);
                    }}
                    className="w-12 h-12 bg-[var(--accent-primary)] hover:bg-[#ff8800] text-black rounded-none flex items-center justify-center shadow-lg transform hover:scale-105 transition-all"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-6 w-6 pl-1"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Metadata Area */}
              <div className="p-3 flex flex-col flex-grow border-t border-[var(--border-color)]">
                <h3
                  className="font-bold text-xs text-white truncate font-mono uppercase tracking-tight"
                  title={title}
                >
                  {title}
                </h3>
                <p
                  className="text-[10px] text-[var(--text-secondary)] truncate mt-1 font-mono uppercase"
                  title={artist}
                >
                  {artist}
                </p>

                <div className="mt-auto pt-2 flex items-center justify-between text-[10px] text-[#ff6b00] font-mono">
                  <span className="truncate">
                    {tags.bpm ? `${tags.bpm} BPM` : ""}
                  </span>
                  <span className="truncate ml-2">{tags.initialKey || ""}</span>
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
