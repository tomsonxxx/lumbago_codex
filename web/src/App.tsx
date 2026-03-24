import { useEffect, useMemo, useState } from "react";
import { getTracks } from "./api/client";
import { AudioPlayer } from "./components/AudioPlayer";
import { DuplicateFinderModal } from "./components/DuplicateFinderModal";
import { ImportWizardModal } from "./components/ImportWizardModal";
import type { Track } from "./types";
import { filterTracks } from "./utils/filterTracks";

export function App() {
  const [libraryTracks, setLibraryTracks] = useState<Track[]>([]);
  const [search, setSearch] = useState("");
  const [keyFilter, setKeyFilter] = useState("");
  const [showImport, setShowImport] = useState(false);
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void refreshTracks();
  }, []);

  async function refreshTracks() {
    setLoading(true);
    try {
      const rows = await getTracks();
      setLibraryTracks(rows);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udalo sie pobrac biblioteki.");
    } finally {
      setLoading(false);
    }
  }

  const tracks = useMemo(
    () => filterTracks(libraryTracks, { search, key: keyFilter }),
    [libraryTracks, search, keyFilter]
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
        <button onClick={() => void refreshTracks()}>Odswiez</button>
      </div>

      <div className="card">
        {loading ? <div className="muted">Ladowanie biblioteki...</div> : null}
        {error ? <div className="error">{error}</div> : null}
        <h3>Library ({tracks.length})</h3>
        <ul>
          {tracks.map((t) => (
            <li key={t.id}>
              {t.artist} - {t.title} [{t.key ?? "-"}]
            </li>
          ))}
        </ul>
      </div>

      <AudioPlayer src="/sample.mp3" />

      <ImportWizardModal
        open={showImport}
        onClose={() => setShowImport(false)}
        onImported={() => void refreshTracks()}
      />
      <DuplicateFinderModal
        open={showDuplicates}
        onClose={() => setShowDuplicates(false)}
      />
    </main>
  );
}
