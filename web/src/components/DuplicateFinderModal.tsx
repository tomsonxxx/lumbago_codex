import { useMemo, useState } from "react";
import type { Track } from "../types";

type Props = {
  open: boolean;
  tracks: Track[];
  onClose: () => void;
};

type Mode = "hash" | "fingerprint" | "metadata";

function groupDuplicates(tracks: Track[], mode: Mode): Track[][] {
  const buckets = new Map<string, Track[]>();
  for (const track of tracks) {
    const key =
      mode === "hash"
        ? track.hash ?? ""
        : mode === "fingerprint"
          ? track.fingerprint ?? ""
          : `${track.title.toLowerCase()}|${track.artist.toLowerCase()}`;
    if (!key) continue;
    const current = buckets.get(key) ?? [];
    current.push(track);
    buckets.set(key, current);
  }
  return [...buckets.values()].filter((g) => g.length > 1);
}

export function DuplicateFinderModal({ open, tracks, onClose }: Props) {
  const [mode, setMode] = useState<Mode>("hash");
  const groups = useMemo(() => groupDuplicates(tracks, mode), [tracks, mode]);
  const [removed, setRemoved] = useState<number[]>([]);

  if (!open) return null;

  function keepFirst(group: Track[]) {
    const idsToRemove = group.slice(1).map((x) => x.id);
    setRemoved((prev) => [...prev, ...idsToRemove]);
  }

  return (
    <div className="modal">
      <div className="card">
        <h3>Duplicate Finder</h3>
        <div className="row">
          <label>Tryb:</label>
          <select value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
            <option value="hash">hash</option>
            <option value="fingerprint">fingerprint</option>
            <option value="metadata">metadata</option>
          </select>
        </div>
        <div className="muted">Wykryte grupy: {groups.length}</div>
        {groups.map((group, idx) => (
          <div key={idx} className="group">
            <strong>Grupa {idx + 1}</strong>
            <ul>
              {group.map((track) => (
                <li key={track.id}>
                  #{track.id} {track.artist} - {track.title}
                  {removed.includes(track.id) ? " (usuniety)" : ""}
                </li>
              ))}
            </ul>
            <button onClick={() => keepFirst(group)}>Keep first / delete rest</button>
          </div>
        ))}
        <div className="row">
          <button onClick={onClose}>Zamknij</button>
        </div>
      </div>
    </div>
  );
}

