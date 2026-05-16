import { useEffect, useState } from "react";
import { updateTrack } from "../api/client";
import type { Track, TrackUpdate } from "../types";

type Props = {
  track: Track;
  onSaved: (updated: Track) => void;
  onClose: () => void;
};

type Draft = {
  title: string;
  artist: string;
  album: string;
  year: string;
  genre: string;
  bpm: string;
  key: string;
  mood: string;
  comment: string;
};

function trackToDraft(track: Track): Draft {
  return {
    title:   track.title  ?? "",
    artist:  track.artist ?? "",
    album:   track.album  ?? "",
    year:    track.year   ?? "",
    genre:   track.genre  ?? "",
    bpm:     track.bpm    != null ? String(track.bpm) : "",
    key:     track.key    ?? "",
    mood:    "",
    comment: track.comment ?? "",
  };
}

export function TrackEditPanel({ track, onSaved, onClose }: Props) {
  const [draft, setDraft] = useState<Draft>(() => trackToDraft(track));
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);

  useEffect(() => {
    setDraft(trackToDraft(track));
    setStatus(null);
  }, [track]);

  function patch(field: keyof Draft, value: string) {
    setDraft((d) => ({ ...d, [field]: value }));
    setStatus(null);
  }

  async function save() {
    if (!track.path) {
      setStatus({ ok: false, msg: "Brak ścieżki pliku — nie można zapisać." });
      return;
    }

    const update: TrackUpdate = {};
    // Wyślij "" (pusty string) gdy użytkownik wyczyścił pole — backend (exclude_none=True)
    // ignoruje null, ale akceptuje "", co faktycznie usuwa wartość z bazy i pliku audio.
    if (draft.title   !== (track.title   ?? "")) update.title   = draft.title;
    if (draft.artist  !== (track.artist  ?? "")) update.artist  = draft.artist;
    if (draft.album   !== (track.album   ?? "")) update.album   = draft.album;
    if (draft.year    !== (track.year    ?? "")) update.year    = draft.year;
    if (draft.genre   !== (track.genre   ?? "")) update.genre   = draft.genre;
    if (draft.key     !== (track.key     ?? "")) update.key     = draft.key;
    if (draft.comment !== (track.comment ?? "")) update.comment = draft.comment;

    const bpmNum = draft.bpm.trim() !== "" ? parseFloat(draft.bpm) : null;
    if (bpmNum !== (track.bpm ?? null)) update.bpm = bpmNum;

    if (Object.keys(update).length === 0) {
      setStatus({ ok: true, msg: "Brak zmian." });
      return;
    }

    setSaving(true);
    setStatus(null);
    try {
      const updated = await updateTrack(track.path, update);
      onSaved(updated);
      setStatus({ ok: true, msg: "✓ Zapisano i zaktualizowano plik audio." });
    } catch (err) {
      setStatus({ ok: false, msg: err instanceof Error ? err.message : "Błąd zapisu." });
    } finally {
      setSaving(false);
    }
  }

  function reset() {
    setDraft(trackToDraft(track));
    setStatus(null);
  }

  return (
    <div className="track-edit-panel">
      <div className="track-edit-header">
        <div>
          <strong className="track-edit-title">{track.title || track.path?.split(/[\\/]/).pop() || "—"}</strong>
          <span className="track-edit-artist">{track.artist || "—"}</span>
        </div>
        <button className="btn-icon" onClick={onClose} title="Zamknij">✕</button>
      </div>

      <div className="track-edit-fields">
        <Field label="Tytuł"   value={draft.title}   onChange={(v) => patch("title",   v)} />
        <Field label="Artysta" value={draft.artist}  onChange={(v) => patch("artist",  v)} />
        <Field label="Album"   value={draft.album}   onChange={(v) => patch("album",   v)} />
        <div className="field-row-2">
          <Field label="Rok"     value={draft.year}    onChange={(v) => patch("year",    v)} />
          <Field label="Gatunek" value={draft.genre}   onChange={(v) => patch("genre",   v)} />
        </div>
        <div className="field-row-2">
          <Field label="BPM"     value={draft.bpm}     onChange={(v) => patch("bpm",     v)} type="number" />
          <Field label="Tonacja" value={draft.key}      onChange={(v) => patch("key",     v)} placeholder="np. 8A" />
        </div>
        <Field label="Komentarz" value={draft.comment} onChange={(v) => patch("comment", v)} multiline />
      </div>

      <div className="track-edit-path">
        <span title={track.path ?? ""}>{track.path ?? "—"}</span>
      </div>

      {status ? (
        <div className={status.ok ? "flash" : "error"}>{status.msg}</div>
      ) : null}

      <div className="track-edit-actions">
        <button onClick={reset} disabled={saving}>Resetuj</button>
        <button className="btn-primary" onClick={() => void save()} disabled={saving}>
          {saving ? "Zapisywanie..." : "Zapisz"}
        </button>
      </div>
    </div>
  );
}

type FieldProps = {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  multiline?: boolean;
};

function Field({ label, value, onChange, type = "text", placeholder, multiline }: FieldProps) {
  return (
    <label className="edit-field">
      <span className="edit-field-label">{label}</span>
      {multiline ? (
        <textarea
          className="edit-field-input"
          value={value}
          rows={2}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          className="edit-field-input"
          type={type}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </label>
  );
}
