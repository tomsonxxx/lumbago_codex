import React, { useRef, useState, useEffect, useCallback } from 'react';
import { AudioFile } from '../types';
import { formatDuration } from '../utils/audioUtils';

interface PlayerViewProps {
  files: AudioFile[];
  currentFileId: string | null;
  onFileChange: (id: string | null) => void;
}

const PlayerView: React.FC<PlayerViewProps> = ({ files, currentFileId, onFileChange }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const objectUrlRef = useRef<string | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);

  const currentFile = files.find(f => f.id === currentFileId) || null;
  const currentIdx = files.findIndex(f => f.id === currentFileId);
  const tags = currentFile?.fetchedTags || currentFile?.originalTags;

  // Load audio when file changes
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (objectUrlRef.current) { URL.revokeObjectURL(objectUrlRef.current); objectUrlRef.current = null; }
    cancelAnimationFrame(animFrameRef.current);

    if (!currentFile || currentFile.file.size === 0) {
      audio.src = ''; setIsPlaying(false); setCurrentTime(0); setDuration(0);
      return;
    }

    const url = URL.createObjectURL(currentFile.file);
    objectUrlRef.current = url;
    audio.src = url;
    audio.volume = volume;

    // Setup Web Audio analyser
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext();
    }
    const ctx = audioCtxRef.current;
    if (ctx.state === 'suspended') ctx.resume();

    if (sourceRef.current) { try { sourceRef.current.disconnect(); } catch {} }
    analyserRef.current = ctx.createAnalyser();
    analyserRef.current.fftSize = 256;
    sourceRef.current = ctx.createMediaElementSource(audio);
    sourceRef.current.connect(analyserRef.current);
    analyserRef.current.connect(ctx.destination);

    audio.play().then(() => { setIsPlaying(true); drawWaveform(); }).catch(() => setIsPlaying(false));
  }, [currentFile?.id]);

  useEffect(() => { if (audioRef.current) audioRef.current.volume = volume; }, [volume]);
  useEffect(() => { return () => { cancelAnimationFrame(animFrameRef.current); if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current); }; }, []);

  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const bufLen = analyser.frequencyBinCount;
    const data = new Uint8Array(bufLen);

    const draw = () => {
      animFrameRef.current = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(data);
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barW = (canvas.width / bufLen) * 2.5;
      let x = 0;
      for (let i = 0; i < bufLen; i++) {
        const h = (data[i] / 255) * canvas.height;
        const gradient = ctx.createLinearGradient(0, canvas.height - h, 0, canvas.height);
        gradient.addColorStop(0, 'rgba(0,212,255,0.9)');
        gradient.addColorStop(1, 'rgba(139,92,246,0.4)');
        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - h, barW, h);
        x += barW + 1;
      }
    };
    draw();
  }, []);

  const handlePlayPause = () => {
    const audio = audioRef.current;
    if (!audio || !currentFile || currentFile.file.size === 0) return;
    if (isPlaying) { audio.pause(); cancelAnimationFrame(animFrameRef.current); }
    else { audio.play().then(() => drawWaveform()).catch(() => {}); }
  };

  const handlePrev = () => { if (currentIdx > 0) onFileChange(files[currentIdx - 1].id); };
  const handleNext = () => { if (currentIdx < files.length - 1) onFileChange(files[currentIdx + 1].id); };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const val = parseFloat(e.target.value);
    audio.currentTime = val;
    setCurrentTime(val);
  };

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', display: 'flex', gap: 24, alignItems: 'flex-start' }}>
      {/* Main player */}
      <div style={{ flex: 1 }}>
        {/* Album art */}
        <div style={{
          width: '100%', maxWidth: 320, aspectRatio: '1',
          borderRadius: 20, overflow: 'hidden', margin: '0 auto 24px',
          background: 'linear-gradient(135deg, rgba(0,212,255,0.2), rgba(139,92,246,0.2))',
          border: '1px solid rgba(0,212,255,0.2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 40px rgba(0,212,255,0.15)',
        }}>
          {tags?.albumCoverUrl ? (
            <img src={tags.albumCoverUrl} alt="okładka" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" strokeWidth="1" opacity={0.4}>
              <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
            </svg>
          )}
        </div>

        {/* Track info */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h2 style={{ color: '#e6f7ff', fontSize: 22, fontWeight: 700, margin: '0 0 6px' }}>
            {tags?.title || currentFile?.file.name || 'Wybierz utwór'}
          </h2>
          <p style={{ color: '#94a3b8', fontSize: 14, margin: '0 0 4px' }}>{tags?.artist || '—'}</p>
          <p style={{ color: '#64748b', fontSize: 12, margin: 0 }}>{tags?.album || '—'}</p>
        </div>

        {/* Waveform */}
        <canvas
          ref={canvasRef}
          width={600} height={80}
          id="waveform-canvas"
          style={{ width: '100%', height: 80, marginBottom: 16, opacity: currentFile ? 1 : 0.3 }}
        />

        {/* Seekbar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <span style={{ fontSize: 12, color: '#94a3b8', width: 40, textAlign: 'right' }}>
            {formatDuration(currentTime)}
          </span>
          <div style={{ flex: 1, position: 'relative', height: 20, display: 'flex', alignItems: 'center' }}>
            <div className="progress-track" style={{ position: 'absolute', width: '100%', height: 6, borderRadius: 3 }}>
              <div className="progress-fill" style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%`, height: '100%' }} />
            </div>
            <input type="range" min={0} max={duration || 100} value={currentTime} onChange={handleSeek}
              style={{ position: 'absolute', width: '100%', opacity: 0, cursor: 'pointer', height: 20 }} />
          </div>
          <span style={{ fontSize: 12, color: '#94a3b8', width: 40 }}>
            {formatDuration(currentFile?.duration || duration)}
          </span>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20, marginBottom: 20 }}>
          <button onClick={handlePrev} disabled={currentIdx <= 0}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', opacity: currentIdx <= 0 ? 0.3 : 1 }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>

          <button onClick={handlePlayPause}
            style={{
              width: 64, height: 64, borderRadius: '50%',
              background: currentFile ? 'linear-gradient(135deg, #00d4ff, #8b5cf6)' : 'rgba(255,255,255,0.1)',
              border: 'none', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white',
              boxShadow: currentFile ? '0 0 24px rgba(0,212,255,0.5)' : 'none', transition: 'all 0.2s',
            }}>
            {isPlaying ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
              </svg>
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            )}
          </button>

          <button onClick={handleNext} disabled={currentIdx >= files.length - 1}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', opacity: currentIdx >= files.length - 1 ? 0.3 : 1 }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>
        </div>

        {/* Volume */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'center' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
          </svg>
          <input type="range" min={0} max={1} step={0.01} value={volume}
            onChange={e => setVolume(parseFloat(e.target.value))} style={{ width: 120 }} />
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
            <path d="M15.54 8.46a5 5 0 010 7.07"/><path d="M19.07 4.93a10 10 0 010 14.14"/>
          </svg>
        </div>

        <audio ref={audioRef}
          onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime || 0)}
          onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={handleNext}
          style={{ display: 'none' }}
        />
      </div>

      {/* Right panel: metadata + queue */}
      <div style={{ width: 260, flexShrink: 0 }}>
        {/* Metadata */}
        {currentFile && (
          <div style={{
            background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
            borderRadius: 12, padding: 16, marginBottom: 16,
          }}>
            <h4 style={{ color: '#e6f7ff', fontSize: 13, fontWeight: 600, margin: '0 0 12px' }}>Informacje</h4>
            {[
              { label: 'BPM', value: tags?.bpm?.toString(), color: '#00d4ff' },
              { label: 'Tonacja', value: tags?.key, color: '#8b5cf6' },
              { label: 'Gatunek', value: tags?.genre, color: '#ec4899' },
              { label: 'Format', value: currentFile.file.type.split('/')[1]?.toUpperCase(), color: '#fbbf24' },
              { label: 'Czas', value: formatDuration(currentFile.duration || duration), color: '#4ade80' },
            ].map(m => (
              <div key={m.label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontSize: 12, color: '#64748b' }}>{m.label}</span>
                <span style={{ fontSize: 12, color: m.color || '#e6f7ff', fontWeight: 600 }}>{m.value || '—'}</span>
              </div>
            ))}
          </div>
        )}

        {/* Queue */}
        <div style={{
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: 12, padding: 16, maxHeight: 400, overflowY: 'auto',
        }}>
          <h4 style={{ color: '#e6f7ff', fontSize: 13, fontWeight: 600, margin: '0 0 12px' }}>
            Kolejka ({files.length})
          </h4>
          {files.length === 0 && (
            <p style={{ color: '#64748b', fontSize: 12 }}>Brak plików w bibliotece</p>
          )}
          {files.slice(0, 30).map((f, i) => {
            const t = f.fetchedTags || f.originalTags;
            const isCurrent = f.id === currentFileId;
            return (
              <div
                key={f.id}
                onClick={() => onFileChange(f.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '7px 8px', borderRadius: 6, cursor: 'pointer',
                  background: isCurrent ? 'rgba(0,212,255,0.1)' : 'transparent',
                  border: `1px solid ${isCurrent ? 'rgba(0,212,255,0.3)' : 'transparent'}`,
                  marginBottom: 2, transition: 'all 0.1s',
                }}
              >
                <span style={{ fontSize: 11, color: isCurrent ? '#00d4ff' : '#64748b', width: 18, textAlign: 'center' }}>
                  {isCurrent ? '▶' : i + 1}
                </span>
                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <div style={{ fontSize: 12, color: isCurrent ? '#00d4ff' : '#e6f7ff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {t?.title || f.file.name}
                  </div>
                  <div style={{ fontSize: 10, color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {t?.artist || ''}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PlayerView;
