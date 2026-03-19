import { useEffect, useMemo, useRef, useState } from "react";

type Props = {
  src: string;
};

export function AudioPlayer({ src }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [error, setError] = useState<string>("");
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const audio = new Audio(src);
    audio.preload = "metadata";
    audioRef.current = audio;

    const onLoaded = () => {
      setDuration(audio.duration || 0);
      setError("");
    };
    const onError = () => {
      setPlaying(false);
      setError("Blad odtwarzania pliku audio.");
      if (retryCount < 1) {
        setRetryCount((v) => v + 1);
        audio.load();
      }
    };
    const onTimeUpdate = () => setTime(audio.currentTime || 0);
    const onEnded = () => setPlaying(false);

    audio.addEventListener("loadedmetadata", onLoaded);
    audio.addEventListener("error", onError);
    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.pause();
      audio.removeEventListener("loadedmetadata", onLoaded);
      audio.removeEventListener("error", onError);
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("ended", onEnded);
    };
  }, [src, retryCount]);

  const label = useMemo(() => (playing ? "Pauza" : "Play"), [playing]);

  function toggle() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }
    audio
      .play()
      .then(() => {
        setPlaying(true);
        setError("");
      })
      .catch(() => {
        setError("Nie udalo sie uruchomic odtwarzania.");
        setPlaying(false);
      });
  }

  function seek(value: number) {
    const audio = audioRef.current;
    if (!audio || !Number.isFinite(value)) return;
    audio.currentTime = value;
    setTime(value);
  }

  return (
    <div className="card">
      <h3>Player</h3>
      <button onClick={toggle}>{label}</button>
      <input
        type="range"
        min={0}
        max={Math.max(duration, 0)}
        step={0.1}
        value={Math.min(time, duration || 0)}
        onChange={(e) => seek(Number(e.target.value))}
      />
      <div className="muted">
        {time.toFixed(1)} / {duration.toFixed(1)} s
      </div>
      {error ? <div className="error">{error}</div> : null}
    </div>
  );
}

