
import React, { useState, useEffect, useRef } from 'react';
import { AudioFile, CuePoint } from '../types';
import AlbumCover from './AlbumCover';

interface PlayerDockProps {
  activeFile: AudioFile | null;
  onUpdateFile?: (id: string, updates: Partial<AudioFile>) => void;
}

const CUE_COLORS = [
    '#f43f5e', // Red (1)
    '#f97316', // Orange (2)
    '#eab308', // Yellow (3)
    '#22c55e', // Green (4)
    '#06b6d4', // Cyan (5)
    '#3b82f6', // Blue (6)
    '#8b5cf6', // Violet (7)
    '#d946ef', // Pink (8)
];

const PlayerDock: React.FC<PlayerDockProps> = ({ activeFile, onUpdateFile }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [cues, setCues] = useState<CuePoint[]>([]);
  
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  
  const [frequencyData, setFrequencyData] = useState<Uint8Array>(new Uint8Array(64).fill(5));
  const isPlayable = activeFile && activeFile.file.size > 0;

  // Initialize cues from file
  useEffect(() => {
      if (activeFile) {
          setCues(activeFile.cues || []);
      } else {
          setCues([]);
      }
  }, [activeFile?.id]);

  useEffect(() => {
    if (!audioRef.current) return;
    if (!audioContextRef.current) {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioContextClass();
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 128;
        try {
            const source = ctx.createMediaElementSource(audioRef.current);
            source.connect(analyser);
            analyser.connect(ctx.destination);
            audioContextRef.current = ctx;
            sourceRef.current = source;
            analyserRef.current = analyser;
        } catch (e) {
            console.warn("Audio setup failed:", e);
        }
    }
  }, []);

  const updateVisualizer = () => {
      if (analyserRef.current && isPlaying) {
          const bufferLength = analyserRef.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          analyserRef.current.getByteFrequencyData(dataArray);
          
          const bars = 40;
          const step = Math.floor(bufferLength / bars);
          const sampledData = new Uint8Array(bars);
          for (let i = 0; i < bars; i++) {
              let sum = 0;
              for(let j=0; j<step; j++) sum += dataArray[i*step + j];
              sampledData[i] = sum / step;
          }
          setFrequencyData(sampledData);
          animationFrameRef.current = requestAnimationFrame(updateVisualizer);
      }
  };

  useEffect(() => {
      if (isPlaying) {
          if (audioContextRef.current?.state === 'suspended') audioContextRef.current.resume();
          updateVisualizer();
      } else {
          if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
          setFrequencyData(prev => prev.map(v => Math.max(5, v * 0.8))); // Decay
      }
      return () => { if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current); }
  }, [isPlaying]);

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
      if (isPlaying) { audio.pause(); setIsPlaying(false); }
      else { audio.play().then(() => setIsPlaying(true)).catch(console.error); }
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

  const handleHotCueClick = (index: number, e: React.MouseEvent) => {
      if (!activeFile || !audioRef.current) return;

      // Check if Cue exists
      const existingCueIndex = cues.findIndex(c => c.id === index);
      
      // Shift+Click to DELETE
      if (e.shiftKey) {
          if (existingCueIndex !== -1) {
              const newCues = cues.filter(c => c.id !== index);
              setCues(newCues);
              if (onUpdateFile) onUpdateFile(activeFile.id, { cues: newCues });
          }
          return;
      }

      // Click to PLAY or SET
      if (existingCueIndex !== -1) {
          // Play from Cue
          audioRef.current.currentTime = cues[existingCueIndex].time;
          if (!isPlaying) {
              audioRef.current.play().then(() => setIsPlaying(true));
          }
      } else {
          // Set Cue
          const newCue: CuePoint = {
              id: index,
              time: audioRef.current.currentTime,
              color: CUE_COLORS[index - 1]
          };
          const newCues = [...cues, newCue];
          setCues(newCues);
          if (onUpdateFile) onUpdateFile(activeFile.id, { cues: newCues });
      }
  };

  const formatTime = (seconds: number) => {
      if (!seconds || isNaN(seconds)) return "0:00";
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const tags = activeFile?.fetchedTags || activeFile?.originalTags;

  return (
    <div className="h-28 bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex items-center px-6 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] z-40 relative">
      <audio ref={audioRef} onTimeUpdate={handleTimeUpdate} onEnded={() => setIsPlaying(false)} crossOrigin="anonymous" />
      
      {/* 1. Track Info */}
      <div className="flex items-center w-1/5 min-w-[200px] pr-4">
        {activeFile ? (
            <div className="flex items-center group">
                <AlbumCover tags={tags} className="w-16 h-16 rounded-lg shadow-lg mr-4 group-hover:scale-105 transition-transform" />
                <div className="overflow-hidden">
                    <div className="text-sm font-bold text-slate-900 dark:text-white truncate neon-text-indigo">{tags?.title || activeFile.file.name}</div>
                    <div className="text-xs font-medium text-indigo-500 truncate mt-0.5">{tags?.artist || 'Unknown Artist'}</div>
                    <div className="text-[10px] text-slate-400 mt-1 font-mono">{formatTime(currentTime)} / {formatTime(duration)}</div>
                </div>
            </div>
        ) : (
            <div className="text-sm text-slate-400 italic">Wybierz utwór...</div>
        )}
      </div>

      {/* 2. Main Controls & Visualization */}
      <div className="flex flex-col items-center justify-center flex-grow max-w-4xl px-4">
        
        {/* Play/Pause & Transport */}
        <div className="flex items-center space-x-6 mb-2">
             <button onClick={togglePlay} className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isPlaying ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/30' : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-indigo-500 hover:text-white'}`}>
                {isPlaying ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 pl-0.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                )}
             </button>
        </div>

        {/* Waveform / Progress */}
        <div className="w-full flex items-center space-x-3 relative">
            <div className="flex-grow h-12 flex items-end justify-between px-1 gap-[2px] bg-slate-100/50 dark:bg-slate-900/50 rounded-lg overflow-hidden relative cursor-pointer group" onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                if(duration) audioRef.current!.currentTime = ((e.clientX - rect.left) / rect.width) * duration;
            }}>
                {/* Hot Cue Markers */}
                {cues.map(cue => (
                    <div 
                        key={cue.id}
                        className="absolute bottom-0 w-0.5 h-full z-10 pointer-events-none"
                        style={{ left: `${(cue.time / duration) * 100}%`, backgroundColor: cue.color }}
                    >
                        <div className="absolute bottom-full mb-1 -ml-1 text-[8px] font-bold text-white bg-black/50 px-1 rounded" style={{ color: cue.color }}>{cue.id}</div>
                    </div>
                ))}

                {Array.from(frequencyData).map((value, idx) => {
                    const heightPercent = Math.max(10, (Number(value) / 255) * 100);
                    const isPlayed = (idx / frequencyData.length) * 100 <= progress;
                    return (
                        <div 
                            key={idx} 
                            className={`w-full rounded-t-sm transition-all duration-75 ${isPlayed ? 'bg-gradient-to-t from-indigo-600 to-purple-500 opacity-100 neon-border-indigo' : 'bg-slate-300 dark:bg-slate-800 opacity-50'}`}
                            style={{ height: `${heightPercent}%` }}
                        ></div>
                    );
                })}
            </div>
        </div>
      </div>

      {/* 3. Hot Cues Grid & Volume */}
      <div className="w-1/4 flex items-center justify-end pl-4 space-x-4">
         
         {/* Hot Cue Pads */}
         <div className="grid grid-cols-4 gap-2">
            {[1, 2, 3, 4, 5, 6, 7, 8].map(idx => {
                const cue = cues.find(c => c.id === idx);
                return (
                    <button
                        key={idx}
                        onClick={(e) => handleHotCueClick(idx, e)}
                        title={cue ? `Cue ${idx}: ${formatTime(cue.time)} (Shift+Click to delete)` : `Set Hot Cue ${idx}`}
                        className={`w-8 h-8 rounded text-[10px] font-bold flex items-center justify-center transition-all shadow-sm border
                            ${cue 
                                ? 'text-white border-transparent hover:brightness-110 active:scale-95' 
                                : 'bg-slate-100 dark:bg-slate-800 text-slate-400 border-slate-300 dark:border-slate-700 hover:text-slate-600 dark:hover:text-slate-300'
                            }
                        `}
                        style={cue ? { backgroundColor: cue.color, boxShadow: `0 0 10px ${cue.color}40` } : {}}
                    >
                        {idx}
                    </button>
                )
            })}
         </div>

         {/* Volume */}
         <input type="range" min="0" max="1" step="0.01" value={volume} onChange={(e) => {
             const v = parseFloat(e.target.value);
             setVolume(v);
             if(audioRef.current) audioRef.current.volume = v;
         }} className="w-20 h-1.5 bg-slate-300 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-indigo-600 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-125" />
      </div>
    </div>
  );
};

export default PlayerDock;
