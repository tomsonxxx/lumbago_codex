import { useMemo, useState } from "react";
import { AudioPlayer } from "./components/AudioPlayer";
import { DuplicateFinderModal } from "./components/DuplicateFinderModal";
import { ImportWizardModal } from "./components/ImportWizardModal";
import type { Track } from "./types";
import { filterTracks } from "./utils/filterTracks";

const DEMO_TRACKS: Track[] = [
  { id: 1, title: "Sunrise", artist: "A", key: "8A", hash: "h1", fingerprint: "f1", url: "" },
  { id: 2, title: "Sunrise", artist: "A", key: "Am", hash: "h1", fingerprint: "f1", url: "" },
  { id: 3, title: "Night Drive", artist: "B", key: "10B", hash: "h3", fingerprint: "f3", url: "" }
];

export function App() {
  const [search, setSearch] = useState("");
  const [keyFilter, setKeyFilter] = useState("");
  const [showImport, setShowImport] = useState(false);
  const [showDuplicates, setShowDuplicates] = useState(false);

  const tracks = useMemo(
    () => filterTracks(DEMO_TRACKS, { search, key: keyFilter }),
    [search, keyFilter]
  );

  return (
    <main className="layout">
      <h1>Lumbago Web (MVP)</h1>
      <div className="card row">
        <input
          placeholder="Szukaj"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <input
          placeholder="Filtr key (np. 8A, Am)"
          value={keyFilter}
          onChange={(e) => setKeyFilter(e.target.value)}
        />
        <button onClick={() => setShowImport(true)}>Import Wizard</button>
        <button onClick={() => setShowDuplicates(true)}>Duplicate Finder</button>
      </div>

      <div className="card">
        <h3>Library ({tracks.length})</h3>
        <ul>
          {tracks.map((t) => (
            <li key={t.id}>
              {t.artist} - {t.title} [{t.key}]
            </li>
          ))}
        </ul>
      </div>

      <AudioPlayer src="/sample.mp3" />

      <ImportWizardModal open={showImport} onClose={() => setShowImport(false)} />
      <DuplicateFinderModal
        open={showDuplicates}
        tracks={DEMO_TRACKS}
        onClose={() => setShowDuplicates(false)}
      />
    </main>
  );
}

