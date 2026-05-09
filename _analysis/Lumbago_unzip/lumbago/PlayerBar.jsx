// Lumbago — Real Audio Player
const { useState, useEffect, useRef } = React;

function PlayerBar({ track, onNext, onPrev }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [pos, setPos] = useState(0);
  const [duration, setDuration] = useState(0);
  const [vol, setVol] = useState(80);
  const [loading, setLoading] = useState(false);
  const blobUrlRef = useRef(null);

  // Load new track
  useEffect(() => {
    if (!track) return;
    const audio = audioRef.current;
    if (!audio) return;

    // Clean up old blob URL
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }

    if (track.file) {
      setLoading(true);
      const url = URL.createObjectURL(track.file);
      blobUrlRef.current = url;
      audio.src = url;
      audio.load();
      audio.play().then(() => { setPlaying(true); setLoading(false); }).catch(() => setLoading(false));
    }
  }, [track?.id]);

  // Volume
  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = vol / 100;
  }, [vol]);

  // Audio events
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onTime = () => setPos(audio.currentTime);
    const onMeta = () => setDuration(audio.duration || 0);
    const onEnd  = () => { setPlaying(false); setPos(0); onNext(); };
    const onPlay = () => setPlaying(true);
    const onPause= () => setPlaying(false);
    audio.addEventListener('timeupdate', onTime);
    audio.addEventListener('loadedmetadata', onMeta);
    audio.addEventListener('ended', onEnd);
    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);
    return () => {
      audio.removeEventListener('timeupdate', onTime);
      audio.removeEventListener('loadedmetadata', onMeta);
      audio.removeEventListener('ended', onEnd);
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
    };
  }, [onNext]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio || !track) return;
    if (playing) audio.pause(); else audio.play().catch(()=>{});
  };

  const seek = (e) => {
    const audio = audioRef.current;
    if (!audio || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    audio.currentTime = ratio * duration;
    setPos(audio.currentTime);
  };

  const fmt = s => {
    if (!s || isNaN(s)) return '0:00';
    return `${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
  };

  const pct = duration > 0 ? (pos / duration) * 100 : 0;

  return (
    <div className="lmb-player">
      {/* Hidden audio element */}
      <audio ref={audioRef} preload="auto" />

      {/* Track info */}
      <div className="lmb-player-info">
        {track ? (
          <>
            <CoverArt track={track} size={44} />
            <div style={{minWidth:0}}>
              <div className="lmb-player-title">{track.title}</div>
              <div className="lmb-player-artist">{track.artist || track.filename}</div>
            </div>
            {track.key && <KeyBadge k={track.key} />}
            {track.bpm && <span className="lmb-bpm">{track.bpm}</span>}
          </>
        ) : (
          <div style={{color:'var(--text-muted)',fontSize:13}}>Brak aktywnego utworu</div>
        )}
      </div>

      {/* Controls + Timeline */}
      <div className="lmb-player-center">
        <div className="lmb-player-controls">
          <button className="lmb-ctrl-btn" onClick={onPrev} title="Poprzedni">⏮</button>
          <button className="lmb-ctrl-play lmb-ctrl-btn" onClick={togglePlay} disabled={!track || loading} title={playing?'Pauza':'Odtwórz'}>
            {loading ? '…' : playing ? '⏸' : '▶'}
          </button>
          <button className="lmb-ctrl-btn" onClick={onNext} title="Następny">⏭</button>
        </div>
        <div className="lmb-player-timeline">
          <span className="lmb-player-time">{fmt(pos)}</span>
          <div className="lmb-player-bar" onClick={seek}>
            <div className="lmb-player-bar-fill" style={{width:`${pct}%`}} />
            {track && <div className="lmb-player-bar-handle" style={{left:`${pct}%`}} />}
          </div>
          <span className="lmb-player-time">{fmt(duration || track?.durationSec)}</span>
        </div>
      </div>

      {/* Volume */}
      <div className="lmb-player-right">
        <button className="lmb-ctrl-btn" onClick={()=>setVol(v=>v>0?0:80)}>
          {vol===0?'🔇':vol<40?'🔉':'🔊'}
        </button>
        <input type="range" min={0} max={100} value={vol}
          onChange={e=>setVol(Number(e.target.value))} className="lmb-vol-slider" />
        <span style={{fontSize:11,color:'var(--text-muted)',width:28}}>{vol}%</span>
      </div>
    </div>
  );
}

Object.assign(window, { PlayerBar });
