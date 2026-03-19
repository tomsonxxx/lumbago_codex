import React, { useEffect, useRef, useState } from 'react';
import { AudioFile } from '../types';
import AlbumCover from './AlbumCover';
import AudioVisualizer from './AudioVisualizer';

interface GlobalPlayerProps {
  currentFile: AudioFile | null;
  isPlaying: boolean;
  volume: number;
  onPlayPause: () => void;
  onVolumeChange: (volume: number) => void;
  onNext: () => void;
  onPrev: () => void;
  onClose: () => void;
}

const GlobalPlayer: React.FC<GlobalPlayerProps> = ({
  currentFile,
  isPlaying,
  volume,
  onPlayPause,
  onVolumeChange,
  onNext,
  onPrev,
  onClose
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<MediaElementAudioSourceNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  // Inicjalizacja Web Audio API
  useEffect(() => {
    if (!audioRef.current) return;

    if (!audioContextRef.current) {
      // Lazy init context (browsers block autoplay if created too early)
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioContextClass();
      const analyserNode = ctx.createAnalyser();
      analyserNode.fftSize = 256;
      
      const source = ctx.createMediaElementSource(audioRef.current);
      source.connect(analyserNode);
      analyserNode.connect(ctx.destination);

      audioContextRef.current = ctx;
      sourceNodeRef.current = source;
      analyserRef.current = analyserNode;
      setAnalyser(analyserNode);
    }
  }, [currentFile]); // Re-check when file changes, but ctx is singleton

  // Obsługa zmiany pliku
  useEffect(() => {
    if (currentFile) {
      if (blobUrl) URL.revokeObjectURL(blobUrl);
      const newUrl = URL.createObjectURL(currentFile.file);
      setBlobUrl(newUrl);
    }
    return () => {
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [currentFile?.id]); // Only change if ID changes

  // Sterowanie odtwarzaniem
  useEffect(() => {
    if (!audioRef.current || !blobUrl) return;

    if (audioRef.current.src !== blobUrl) {
       audioRef.current.src = blobUrl;
       audioRef.current.load();
    }

    if (isPlaying) {
      // Resume context if suspended (browser policy)
      if (audioContextRef.current?.state === 'suspended') {
        audioContextRef.current.resume();
      }
      audioRef.current.play().catch(e => console.error("Playback failed:", e));
    } else {
      audioRef.current.pause();
    }
  }, [blobUrl, isPlaying]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      setDuration(audioRef.current.duration || 0);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = Number(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  if (!currentFile) return null;

  const displayTags = currentFile.fetchedTags || currentFile.originalTags;
  const title = displayTags.title || currentFile.file.name;
  const artist = displayTags.artist || 'Nieznany Artysta';

  const formatTime = (time: number) => {
    const min = Math.floor(time / 60);
    const sec = Math.floor(time % 60);
    return `${min}:${sec < 10 ? '0' : ''}${sec}`;
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] z-50 transition-transform duration-300 animate-slide-up">
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onEnded={onNext}
        onLoadedMetadata={handleTimeUpdate}
      />
      
      <div className="max-w-screen-2xl mx-auto px-4 py-2 flex items-center justify-between gap-4 h-20">
        
        {/* Info & Visualizer */}
        <div className="flex items-center w-1/4 min-w-[200px] gap-3">
           <AlbumCover tags={displayTags} className="w-14 h-14 shadow-md" />
           <div className="flex flex-col min-w-0">
              <span className="font-bold text-slate-900 dark:text-white truncate text-sm">{title}</span>
              <span className="text-xs text-slate-500 dark:text-slate-400 truncate">{artist}</span>
           </div>
        </div>

        {/* Controls & Scrubber */}
        <div className="flex flex-col items-center flex-grow max-w-xl">
           <div className="flex items-center gap-6 mb-1">
              <button onClick={onPrev} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              </button>
              
              <button 
                onClick={onPlayPause} 
                className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-500 hover:scale-105 transition-all shadow-lg"
              >
                 {isPlaying ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                 ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 pl-0.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                 )}
              </button>

              <button onClick={onNext} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              </button>
           </div>
           
           <div className="w-full flex items-center gap-3 text-xs text-slate-500 font-mono">
              <span>{formatTime(currentTime)}</span>
              <input
                type="range"
                min="0"
                max={duration || 100}
                value={currentTime}
                onChange={handleSeek}
                className="flex-grow h-1 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
              <span>{formatTime(duration)}</span>
           </div>
        </div>

        {/* Volume & Visualizer & Close */}
        <div className="flex items-center w-1/4 justify-end gap-4">
           {/* Visualizer Container */}
           <div className="hidden md:block w-32 h-10 bg-slate-100 dark:bg-black/50 rounded overflow-hidden">
              <AudioVisualizer analyser={analyser} isPlaying={isPlaying} />
           </div>

           <div className="flex items-center gap-2 group relative">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" /></svg>
               <input
                 type="range"
                 min="0"
                 max="1"
                 step="0.01"
                 value={volume}
                 onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
                 className="w-20 h-1 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-slate-500"
               />
           </div>
           
           <button onClick={onClose} className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
           </button>
        </div>
      </div>
      <style>{`
        @keyframes slide-up {
            from { transform: translateY(100%); }
            to { transform: translateY(0); }
        }
        .animate-slide-up {
            animation: slide-up 0.3s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default GlobalPlayer;
