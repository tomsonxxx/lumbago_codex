import React, { useRef, useState, useEffect, useCallback } from 'react';
import { AudioFile } from '../types';
import { formatDuration } from '../utils/audioUtils';

interface PlayerBarProps {
  currentFile: AudioFile | null;
  files: AudioFile[];
  onFileChange: (id: string | null) => void;
  onNavigateToPlayer?: () => void;
}

const PlayerBar: React.FC<PlayerBarProps> = ({ currentFile, files, onFileChange, onNavigateToPlayer }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);
  const objectUrlRef = useRef<string | null>(null);

  // Load audio when currentFile changes
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }

    if (!currentFile || currentFile.file.size === 0) {
      audio.src = '';
      setIsPlaying(false);
      setCurrentTime(0);
      setDuration(0);
      return;
    }

    const url = URL.createObjectURL(currentFile.file);
    objectUrlRef.current = url;
    audio.src = url;
    audio.volume = isMuted ? 0 : volume;
    audio.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
  }, [currentFile?.id]);

  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = isMuted ? 0 : volume;
  }, [volume, isMuted]);

  useEffect(() => {
    return () => {
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
  }, []);

  const handlePlayPause = () => {
    const audio = audioRef.current;
    if (!audio || !currentFile || currentFile.file.size === 0) return;
    if (isPlaying) audio.pause();
    else audio.play().catch(() => {});
  };

  const handlePrev = useCallback(() => {
    if (!currentFile) return;
    const idx = files.findIndex(f => f.id === currentFile.id);
    if (idx > 0) onFileChange(files[idx - 1].id);
  }, [currentFile, files, onFileChange]);

  const handleNext = useCallback(() => {
    if (!currentFile) return;
    const idx = files.findIndex(f => f.id === currentFile.id);
    if (idx < files.length - 1) onFileChange(files[idx + 1].id);
  }, [currentFile, files, onFileChange]);

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const val = parseFloat(e.target.value);
    audio.currentTime = val;
    setCurrentTime(val);
  };

  const tags = currentFile?.fetchedTags || currentFile?.originalTags;
  const title = tags?.title || currentFile?.file.name || 'Brak pliku';
  const artist = tags?.artist || '';
  const cover = tags?.albumCoverUrl;

  return (
    <>
      <audio
        ref={audioRef}
        onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime || 0)}
        onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={handleNext}
        style={{ display: 'none' }}
      />
      <div style={{
        position: 'fixed',
        bottom: 0, left: 0, right: 0,
        height: 76,
        background: 'rgba(6,8,22,0.97)',
        borderTop: '1px solid rgba(0,212,255,0.15)',
        backdropFilter: 'blur(20px)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        gap: 16,
        zIndex: 30,
      }}>
        {/* Album art + track info */}
        <div
          style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 220, cursor: onNavigateToPlayer ? 'pointer' : 'default' }}
          onClick={onNavigateToPlayer}
        >
          <div style={{
            width: 48, height: 48, borderRadius: 8, flexShrink: 0,
            overflow: 'hidden',
            background: 'linear-gradient(135deg, rgba(0,212,255,0.2), rgba(139,92,246,0.2))',
            border: '1px solid rgba(0,212,255,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {cover ? (
              <img src={cover} alt="okładka" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" strokeWidth="1.5">
                <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
              </svg>
            )}
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#e6f7ff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 160 }}>
              {title}
            </div>
            <div style={{ fontSize: 11, color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 160 }}>
              {artist || 'Nieznany artysta'}
            </div>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <button
            onClick={handlePrev}
            disabled={!currentFile}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 6, borderRadius: 6, transition: 'color 0.15s' }}
            onMouseEnter={e => (e.currentTarget.style.color = '#e6f7ff')}
            onMouseLeave={e => (e.currentTarget.style.color = '#94a3b8')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>

          <button
            onClick={handlePlayPause}
            disabled={!currentFile || currentFile.file.size === 0}
            style={{
              width: 40, height: 40, borderRadius: '50%',
              background: currentFile ? 'linear-gradient(135deg, #00d4ff, #8b5cf6)' : 'rgba(255,255,255,0.1)',
              border: 'none', cursor: currentFile ? 'pointer' : 'default',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', boxShadow: currentFile ? '0 0 12px rgba(0,212,255,0.4)' : 'none',
              transition: 'all 0.15s',
            }}
          >
            {isPlaying ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            )}
          </button>

          <button
            onClick={handleNext}
            disabled={!currentFile}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 6, borderRadius: 6, transition: 'color 0.15s' }}
            onMouseEnter={e => (e.currentTarget.style.color = '#e6f7ff')}
            onMouseLeave={e => (e.currentTarget.style.color = '#94a3b8')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>
        </div>

        {/* Progress */}
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 11, color: '#94a3b8', flexShrink: 0, width: 35, textAlign: 'right' }}>
            {formatDuration(currentTime)}
          </span>
          <div style={{ flex: 1, position: 'relative', height: 20, display: 'flex', alignItems: 'center' }}>
            <div className="progress-track" style={{ position: 'absolute', width: '100%', height: 4 }}>
              <div
                className="progress-fill"
                style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%`, height: '100%' }}
              />
            </div>
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={handleSeek}
              style={{ position: 'absolute', width: '100%', opacity: 0, cursor: 'pointer', height: 20 }}
            />
          </div>
          <span style={{ fontSize: 11, color: '#94a3b8', flexShrink: 0, width: 35 }}>
            {formatDuration(currentFile?.duration || duration)}
          </span>
        </div>

        {/* Volume */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <button
            onClick={() => setIsMuted(m => !m)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 4 }}
          >
            {isMuted || volume === 0 ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                <path d="M15.54 8.46a5 5 0 010 7.07"/><path d="M19.07 4.93a10 10 0 010 14.14"/>
              </svg>
            )}
          </button>
          <input
            type="range" min={0} max={1} step={0.01}
            value={isMuted ? 0 : volume}
            onChange={e => { setVolume(parseFloat(e.target.value)); setIsMuted(false); }}
            style={{ width: 70 }}
          />
        </div>
      </div>
    </>
  );
};

export default PlayerBar;
