import React, { useState, useEffect } from "react";
import { AudioFile } from "../types";

interface MediaBrowserProps {
  directoryHandle: any;
  files: AudioFile[];
  onPlay: (file: AudioFile) => void;
  onContextMenu?: (e: React.MouseEvent, fileId: string) => void;
  onSelectEntries?: (ids: string[]) => void;
  popularTags?: string[];
  onTagClick?: (tag: string) => void;
}

interface FileEntry {
  name: string;
  kind: "file" | "directory";
  handle: any;
  path: string;
  audioFile?: AudioFile;
}

const MediaBrowser: React.FC<MediaBrowserProps> = ({
  directoryHandle,
  files,
  onPlay,
  onContextMenu,
  onSelectEntries,
  popularTags = [],
  onTagClick,
}) => {
  const [currentPath, setCurrentPath] = useState<string[]>([]);
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadEntries();
  }, [currentPath, directoryHandle, files]);

  const loadEntries = async () => {
    if (!directoryHandle) return;
    setLoading(true);
    try {
      let dir = directoryHandle;
      for (const part of currentPath) {
        dir = await dir.getDirectoryHandle(part);
      }

      const newEntries: FileEntry[] = [];
      for await (const entry of dir.values()) {
        const fullPath = [...currentPath, entry.name].join("/");
        const audioFile = files.find(f => (f.webkitRelativePath || f.file.name) === fullPath || f.file.name === entry.name);
        
        newEntries.push({
          name: entry.name,
          kind: entry.kind,
          handle: entry,
          path: fullPath,
          audioFile
        });
      }

      // Sort: Directories first, then files
      newEntries.sort((a, b) => {
        if (a.kind === b.kind) return a.name.localeCompare(b.name);
        return a.kind === "directory" ? -1 : 1;
      });

      setEntries(newEntries);
    } catch (err) {
      console.error("Browser error:", err);
    } finally {
      setLoading(false);
    }
  };

  const navigateTo = (name: string) => {
    setCurrentPath([...currentPath, name]);
  };

  const navigateUp = () => {
    setCurrentPath(currentPath.slice(0, -1));
  };

  return (
    <div className="flex-grow flex flex-col overflow-hidden bg-black/20 backdrop-blur-sm animate-fade-in">
      {/* Breadcrumbs */}
      <div className="p-4 border-b border-white/5 flex items-center gap-2 overflow-x-auto scrollbar-hide shrink-0">
        <button 
          onClick={() => setCurrentPath([])}
          className="text-white/40 hover:text-[var(--accent-cyan)] transition-colors"
        >
           <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
             <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
           </svg>
        </button>
        {currentPath.map((part, i) => (
          <React.Fragment key={i}>
            <span className="text-white/10">/</span>
            <button 
              onClick={() => setCurrentPath(currentPath.slice(0, i + 1))}
              className="text-xs font-bold text-white/60 hover:text-white whitespace-nowrap"
            >
              {part}
            </button>
          </React.Fragment>
        ))}
      </div>

      {/* Top Bar with Tags */}
      <div className="flex items-center justify-between p-4 border-b border-white/5 bg-white/[0.02]">
         <div className="flex flex-wrap gap-2 overflow-x-auto scrollbar-hide py-1">
            {popularTags.slice(0, 15).map(tag => (
               <button
                 key={tag}
                 onClick={() => onTagClick?.(tag)}
                 className="px-3 py-1 bg-white/5 hover:bg-white/10 rounded-full text-[10px] text-white/50 hover:text-white transition-all whitespace-nowrap"
               >
                 #{tag}
               </button>
            ))}
         </div>
      </div>

      {/* Explorer Area */}
      <div className="flex-grow overflow-y-auto p-4 custom-scrollbar min-h-0">
        {loading ? (
          <div className="h-full flex items-center justify-center">
             <div className="w-10 h-10 border-4 border-[var(--accent-cyan)]/20 border-t-[var(--accent-cyan)] rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4 pb-20">
            {currentPath.length > 0 && (
              <div 
                onClick={navigateUp}
                className="group flex flex-col items-center p-4 rounded-3xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 transition-all cursor-pointer"
              >
                <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center text-white/40 mb-3 group-hover:scale-110 transition-transform">
                   <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                   </svg>
                </div>
                <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">W górę</span>
              </div>
            )}

            {entries.map((entry) => (
              <div 
                key={entry.path}
                onClick={() => entry.kind === 'directory' ? navigateTo(entry.name) : (entry.audioFile && onPlay(entry.audioFile))}
                onContextMenu={(e) => entry.audioFile && onContextMenu?.(e, entry.audioFile.id)}
                className="group relative flex flex-col items-center p-4 rounded-3xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 hover:scale-[1.02] active:scale-95 transition-all cursor-pointer"
              >
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-3 transition-transform group-hover:scale-110 ${
                  entry.kind === 'directory' 
                    ? "bg-[var(--accent-blue)]/20 text-[var(--accent-blue)] glow-blue" 
                    : "bg-[var(--accent-cyan)]/10 text-[var(--accent-cyan)]"
                }`}>
                   {entry.kind === 'directory' ? (
                     <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" viewBox="0 0 20 20" fill="currentColor">
                       <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                     </svg>
                   ) : (
                     <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 18V5l12-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="18" cy="16" r="3" />
                     </svg>
                   )}
                </div>
                <span className="text-[10px] font-bold text-white tracking-tight text-center line-clamp-2 w-full">{entry.name}</span>
                
                {entry.audioFile && (
                  <div className="mt-2 flex gap-1">
                     <span className="px-1.5 py-0.5 rounded bg-[var(--accent-cyan)] text-[8px] font-black text-black">{entry.audioFile.fetchedTags?.initialKey || "—"}</span>
                     <span className="px-1.5 py-0.5 rounded bg-white/10 text-[8px] font-bold text-white/40">{entry.audioFile.fetchedTags?.bpm || "—"}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MediaBrowser;
