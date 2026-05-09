import React, { useState, useEffect, useRef } from "react";
import { AudioFile } from "../types";
import AlbumCover from "./AlbumCover";

interface PlayerDockProps {
  activeFile: AudioFile | null;
  onUpdateFile?: (id: string, updates: Partial<AudioFile>) => void;
}


const PlayerDock: React.FC<PlayerDockProps> = ({
  activeFile,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [isMinimized, setIsMinimized] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const isPlayable = activeFile && activeFile.file.size > 0;

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (activeFile && isPlayable) {
      const objectUrl = URL.createObjectURL(activeFile.file);
      audio.src = objectUrl;
      audio.play().then(() => setIsPlaying(true)).catch(console.warn);
      return () => URL.revokeObjectURL(objectUrl);
    } else {
      audio.pause();
      setIsPlaying(false);
    }
  }, [activeFile?.id, isPlayable]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (audio && isPlayable) {
      if (isPlaying) {
        audio.pause();
        setIsPlaying(false);
      } else {
        audio.play().then(() => setIsPlaying(true)).catch(console.error);
      }
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      const current = audioRef.current.currentTime;
      const total = audioRef.current.duration || 0;
      setCurrentTime(current);
      setDuration(total);
      setProgress((current / total) * 100);
    }
  };

  const formatTime = (seconds: number) => {
    if (!seconds || isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const tags = activeFile?.fetchedTags || activeFile?.originalTags;

  return (
    <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 w-[95%] max-w-7xl glass-effect rounded-2xl transition-all duration-500 z-50 shadow-2xl border border-white/5 ${isMinimized ? 'h-12 px-4' : 'h-20 px-8'}`}>
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => setIsPlaying(false)}
        crossOrigin="anonymous"
      />

      {/* Left: Track Info */}
      <div className={`flex items-center gap-4 ${isMinimized ? 'w-auto' : 'w-1/4'}`}>
        {activeFile ? (
          <>
            <div className={`${isMinimized ? 'w-8 h-8' : 'w-12 h-12'} rounded-lg overflow-hidden border border-white/10 glow-cyan shrink-0 transition-all`}>
              <AlbumCover tags={tags} className="w-full h-full object-cover" />
            </div>
            {!isMinimized && (
              <div className="overflow-hidden">
                <div className="text-sm font-bold text-white truncate font-heading">
                  {tags?.title || activeFile.file.name}
                </div>
                <div className="text-[10px] text-white/40 uppercase tracking-widest truncate">
                  {tags?.artist || "Nieznany Artysta"}
                </div>
              </div>
            )}
          </>
        ) : (
          !isMinimized && (
            <div className="text-sm text-white/20 font-medium tracking-wide">
               Wybierz utwór do odtworzenia
            </div>
          )
        )}
      </div>

      {/* Center: Controls & Progress */}
      <div className={`flex items-center gap-4 flex-1 ${isMinimized ? 'justify-center mx-4' : 'flex-col justify-center max-w-2xl'}`}>
        <div className={`flex items-center ${isMinimized ? 'gap-2' : 'gap-8'}`}>
           {!isMinimized && (
             <button className="p-2 text-white/40 hover:text-white transition-all">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
               </svg>
             </button>
           )}
           
           <button 
             onClick={togglePlay}
             disabled={!isPlayable}
             className={`${isMinimized ? 'w-8 h-8' : 'w-12 h-12'} rounded-full bg-white flex items-center justify-center text-black shadow-lg glow-cyan hover:scale-110 active:scale-95 transition-all shrink-0`}
           >
             {isPlaying ? (
               <svg xmlns="http://www.w3.org/2000/svg" className={`${isMinimized ? 'h-4 w-4' : 'h-6 w-6'}`} viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
             ) : (
               <svg xmlns="http://www.w3.org/2000/svg" className={`${isMinimized ? 'h-4 w-4' : 'h-6 w-6'} ml-0.5`} viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
             )}
           </button>

           {!isMinimized && (
             <button className="p-2 text-white/40 hover:text-white transition-all">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
               </svg>
             </button>
           )}
        </div>

        <div className={`flex items-center gap-4 ${isMinimized ? 'flex-grow max-w-md' : 'w-full'}`}>
          <span className="text-[10px] font-mono text-white/40 min-w-[35px] text-right">
             {formatTime(currentTime)}
          </span>
          <div 
            className={`flex-1 ${isMinimized ? 'h-1' : 'h-1.5'} bg-white/5 rounded-full overflow-hidden cursor-pointer relative transition-all`}
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              if (duration) audioRef.current!.currentTime = ((e.clientX - rect.left) / rect.width) * duration;
            }}
          >
             <div 
               className="h-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-magenta)] shadow-[0_0_10px_rgba(0,212,255,0.5)] transition-all duration-100"
               style={{ width: `${progress}%` }}
             />
             {!isMinimized && (
               <div 
                 className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg border border-white/20 glow-cyan"
                 style={{ left: `calc(${progress}% - 6px)` }}
               />
             )}
          </div>
          <span className="text-[10px] font-mono text-white/40 min-w-[35px]">
             {formatTime(duration)}
          </span>
        </div>
      </div>

      {/* Right: Sound & Tools */}
      <div className={`flex items-center justify-end ${isMinimized ? 'gap-2' : 'gap-6 w-1/4'}`}>
        {!isMinimized && (
          <div className="flex items-center gap-3">
             <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white/40" viewBox="0 0 20 20" fill="currentColor">
               <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 14.657a1 1 0 01-1.414-1.414A5 5 0 0011 8.586V6.172a7 7 0 012.241 2.241a7 7 0 011.416 6.244z" clipRule="evenodd" />
             </svg>
             <input
               type="range"
               min="0"
               max="1"
               step="0.01"
               value={volume}
               onChange={(e) => {
                 const v = parseFloat(e.target.value);
                 setVolume(v);
                 if (audioRef.current) audioRef.current.volume = v;
               }}
               className="w-20 h-1 bg-white/10 rounded-full appearance-none cursor-pointer accent-white"
             />
          </div>
        )}
        
        <div className="flex items-center gap-1">
          <button 
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-all"
            title={isMinimized ? "Rozwiń" : "Zminimalizuj"}
          >
            {isMinimized ? (
               <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
               </svg>
            ) : (
               <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
               </svg>
            )}
          </button>
          {!isMinimized && (
            <button className="p-2 text-white/40 hover:text-white hover:bg-white/5 rounded-lg transition-all">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
               </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerDock;
