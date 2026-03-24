import { useEffect, useState } from "react";
import { analyzeDuplicates } from "../api/client";
import type { DuplicateGroup } from "../types";

type Props = {
  open: boolean;
  onClose: () => void;
};

type Mode = "hash" | "fingerprint" | "metadata";

export function DuplicateFinderModal({ open, onClose }: Props) {
  const [mode, setMode] = useState<Mode>("hash");
  const [groups, setGroups] = useState<DuplicateGroup[]>([]);
  const [removed, setRemoved] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    void analyzeDuplicates(mode)
      .then((result) => {
        setGroups(result.groups);
        setError("");
      })
      .catch((err) => {
        setGroups([]);
        setError(err instanceof Error ? err.message : "Nie udalo sie wykryc duplikatow.");
      })
      .finally(() => setLoading(false));
  }, [open, mode]);

  if (!open) return null;

  function keepFirst(group: DuplicateGroup) {
    const idsToRemove = group.tracks.slice(1).map((x) => x.id);
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
        {loading ? <div className="muted">Analiza duplikatow w toku...</div> : null}
        {error ? <div className="error">{error}</div> : null}
        <div className="muted">Wykryte grupy: {groups.length}</div>
        {groups.map((group, idx) => (
          <div key={idx} className="group">
            <strong>Grupa {idx + 1}</strong>
            <div className="muted">Podobienstwo: {Math.round(group.similarity * 100)}%</div>
            <ul>
              {group.tracks.map((track) => (
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
