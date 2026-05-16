import { useEffect, useMemo, useState } from "react";
import {
  applyAnalysisJob,
  createAnalysisJob,
  getAiProviders,
  getAnalysisJob,
  getTracks,
  updateAiProviders,
} from "./api/client";
import { AudioPlayer } from "./components/AudioPlayer";
import { DuplicateFinderModal } from "./components/DuplicateFinderModal";
import { ImportWizardModal } from "./components/ImportWizardModal";
import { TrackEditPanel } from "./components/TrackEditPanel";
import type { AnalysisJob, ProviderConfig, Track } from "./types";
import { filterTracks } from "./utils/filterTracks";

type TabId = "library" | "scan" | "tagger" | "duplicates" | "settings";

const TABS: { id: TabId; label: string }[] = [
  { id: "library", label: "Biblioteka" },
  { id: "scan", label: "Import / Skan" },
  { id: "tagger", label: "Tagger AI" },
  { id: "duplicates", label: "Duplikaty" },
  { id: "settings", label: "Ustawienia" },
];

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>("library");
  const [libraryTracks, setLibraryTracks] = useState<Track[]>([]);
  const [search, setSearch] = useState("");
  const [keyFilter, setKeyFilter] = useState("");
  const [showImport, setShowImport] = useState(false);
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [analysisJob, setAnalysisJob] = useState<AnalysisJob | null>(null);
  const [runningJobId, setRunningJobId] = useState<string>("");
  const [analysisMessage, setAnalysisMessage] = useState("");
  const [selectedTrack, setSelectedTrack] = useState<Track | null>(null);

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    if (!runningJobId) return;
    const timer = setInterval(() => {
      void pollJob(runningJobId);
    }, 1200);
    return () => clearInterval(timer);
  }, [runningJobId]);

  async function bootstrap() {
    await Promise.all([refreshTracks(), refreshProviders()]);
  }

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

  function handleTrackSaved(updated: Track) {
    setLibraryTracks((prev) =>
      prev.map((t) => (t.id === updated.id ? updated : t))
    );
    setSelectedTrack(updated);
  }

  async function refreshProviders() {
    try {
      const rows = await getAiProviders();
      setProviders(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udalo sie pobrac providerow.");
    }
  }

  async function pollJob(jobId: string) {
    try {
      const job = await getAnalysisJob(jobId);
      setAnalysisJob(job);
      if (job.status === "completed" || job.status === "failed") {
        setRunningJobId("");
      }
    } catch (err) {
      setRunningJobId("");
      setAnalysisMessage(err instanceof Error ? err.message : "Nie udalo sie odczytac joba.");
    }
  }

  async function runTagger() {
    setAnalysisMessage("");
    try {
      const response = await createAnalysisJob(libraryTracks.map((t) => t.id));
      setRunningJobId(response.job_id);
      setActiveTab("tagger");
    } catch (err) {
      setAnalysisMessage(err instanceof Error ? err.message : "Nie udalo sie uruchomic analizy.");
    }
  }

  async function applyTaggerChanges() {
    if (!analysisJob) return;
    try {
      const result = await applyAnalysisJob(analysisJob.id);
      setAnalysisMessage(
        `Zastosowano ${result.applied_changes} zmian w ${result.updated_tracks} utworach.`
      );
      await refreshTracks();
    } catch (err) {
      setAnalysisMessage(err instanceof Error ? err.message : "Nie udalo sie zapisac zmian.");
    }
  }

  async function saveProviders(updated: ProviderConfig[]) {
    const saved = await updateAiProviders(updated);
    setProviders(saved);
    setAnalysisMessage("Zapisano ustawienia providerów.");
  }

  const tracks = useMemo(
    () => filterTracks(libraryTracks, { search, key: keyFilter }),
    [libraryTracks, search, keyFilter]
  );

  return (
    <main className="layout-v2">
      <header className="top-shell">
        <div>
          <h1>Lumbago Music AI</h1>
          <p>Pro dark pro-audio workflow: import, analiza, preview, apply.</p>
        </div>
        <div className="toolbar-actions">
          <button onClick={() => setShowImport(true)}>Import</button>
          <button onClick={runTagger} disabled={libraryTracks.length === 0 || !!runningJobId}>
            {runningJobId ? "Analiza w toku..." : "Start analizy"}
          </button>
          <button onClick={() => setShowDuplicates(true)}>Duplikaty</button>
          <button onClick={() => setShowSettings(true)}>Ustawienia</button>
        </div>
      </header>

      <nav className="tabbar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={activeTab === tab.id ? "tab active" : "tab"}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {analysisMessage ? <div className="flash">{analysisMessage}</div> : null}
      {error ? <div className="error">{error}</div> : null}

      {activeTab === "library" ? (
        <section className="panel library-layout">
          <div className="library-list">
            <div className="row filters">
              <input
                placeholder="Szukaj po bibliotece"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <input
                placeholder="Klucz (8A, Am...)"
                value={keyFilter}
                onChange={(event) => setKeyFilter(event.target.value)}
              />
              <button onClick={() => void refreshTracks()}>Odśwież</button>
            </div>
            <div className="list-head">
              <strong>Biblioteka ({tracks.length})</strong>
              <span>{loading ? "Ładowanie..." : selectedTrack ? "Kliknij track, aby edytować" : "Gotowe"}</span>
            </div>
            <ul className="track-list">
              {tracks.map((track) => (
                <li
                  key={track.id}
                  className={selectedTrack?.id === track.id ? "selected" : ""}
                  onClick={() => setSelectedTrack(track)}
                >
                  <span className="col-artist">{track.artist || "—"}</span>
                  <span className="col-title">{track.title || "—"}</span>
                  <span className="col-album">{track.album ?? "—"}</span>
                  <span className="col-key">{track.key ?? "—"}</span>
                  <span className="col-bpm">{track.bpm ? track.bpm.toFixed(1) : "—"}</span>
                </li>
              ))}
            </ul>
          </div>

          {selectedTrack ? (
            <TrackEditPanel
              track={selectedTrack}
              onSaved={handleTrackSaved}
              onClose={() => setSelectedTrack(null)}
            />
          ) : null}
        </section>
      ) : null}

      {activeTab === "scan" ? (
        <section className="panel">
          <h2>Import / Skan</h2>
          <p className="muted">
            Użyj kreatora importu. Po imporcie biblioteka i tagger odświeżą się automatycznie.
          </p>
          <button onClick={() => setShowImport(true)}>Otwórz Import Wizard</button>
        </section>
      ) : null}

      {activeTab === "tagger" ? (
        <section className="panel">
          <div className="row split">
            <h2>Tagger AI</h2>
            <button
              onClick={applyTaggerChanges}
              disabled={!analysisJob || analysisJob.status !== "completed"}
            >
              Zastosuj zaakceptowane zmiany
            </button>
          </div>
          {!analysisJob ? <p className="muted">Uruchom analizę, aby zobaczyć podgląd zmian.</p> : null}
          {analysisJob ? (
            <>
              <div className="job-meta">
                <span>Status: {analysisJob.status}</span>
                <span>
                  Postęp: {analysisJob.processed}/{analysisJob.total}
                </span>
              </div>
              <div className="job-items">
                {analysisJob.items.map((item) => (
                  <article key={item.track_id} className="job-item">
                    <h4>
                      {item.artist} — {item.title}
                    </h4>
                    <p className="muted">
                      Providers: {item.provider_chain} | Confidence:{" "}
                      {(item.confidence * 100).toFixed(0)}%
                    </p>
                    <ul>
                      {item.decisions
                        .filter((decision) => decision.old_value !== decision.new_value)
                        .slice(0, 8)
                        .map((decision) => (
                          <li key={`${item.track_id}-${decision.field}`}>
                            <strong>{decision.field}</strong>: {String(decision.old_value ?? "—")} →{" "}
                            {String(decision.new_value ?? "—")} ({decision.winner_provider},{" "}
                            {(decision.confidence * 100).toFixed(0)}%)
                          </li>
                        ))}
                    </ul>
                  </article>
                ))}
              </div>
            </>
          ) : null}
        </section>
      ) : null}

      {activeTab === "duplicates" ? (
        <section className="panel">
          <h2>Duplikaty</h2>
          <p className="muted">Otwórz modal duplikatów, aby przeanalizować bibliotekę.</p>
          <button onClick={() => setShowDuplicates(true)}>Otwórz Duplicate Finder</button>
        </section>
      ) : null}

      {activeTab === "settings" ? (
        <section className="panel">
          <div className="row split">
            <h2>Ustawienia API</h2>
            <button onClick={() => setShowSettings(true)}>Edytuj</button>
          </div>
          <ul className="provider-list">
            {providers.map((provider) => (
              <li key={provider.provider}>
                <strong>{provider.provider}</strong>
                <span>{provider.model}</span>
                <span>{provider.base_url}</span>
                <span>{provider.enabled ? "enabled" : "disabled"}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <div className="card">
        {loading ? <div className="muted">Ladowanie biblioteki...</div> : null}
        {error ? <div className="error">{error}</div> : null}
        <h3>Library ({tracks.length})</h3>
        <ul>
          {tracks.map((t) => (
            <li key={t.id}>
              {t.title ?? "-"} | {t.bpm ?? "-"} | {t.key ?? "-"} | {t.artist ?? "-"} | {t.album ?? "-"} |{" "}
              {t.genre ?? "-"} | {t.year ?? "-"} | {t.composer ?? "-"} | {t.comment ?? "-"} | {t.lyrics ?? "-"} |{" "}
              {t.publisher ?? "-"}
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
      <DuplicateFinderModal open={showDuplicates} onClose={() => setShowDuplicates(false)} />
      <SettingsModal
        open={showSettings}
        providers={providers}
        onClose={() => setShowSettings(false)}
        onSave={(updated) => void saveProviders(updated)}
      />
    </main>
  );
}

type SettingsModalProps = {
  open: boolean;
  providers: ProviderConfig[];
  onClose: () => void;
  onSave: (providers: ProviderConfig[]) => void;
};

function SettingsModal({ open, providers, onClose, onSave }: SettingsModalProps) {
  const [draft, setDraft] = useState<ProviderConfig[]>(providers);

  useEffect(() => {
    if (!open) return;
    setDraft(providers);
  }, [open, providers]);

  if (!open) return null;

  function patchProvider(index: number, patch: Partial<ProviderConfig>) {
    setDraft((current) =>
      current.map((item, idx) => (idx === index ? { ...item, ...patch } : item))
    );
  }

  return (
    <div className="modal">
      <div className="card modal-card">
        <h3>Ustawienia dostawców AI</h3>
        <div className="provider-editor">
          {draft.map((provider, index) => (
            <div className="provider-row" key={provider.provider}>
              <h4>{provider.provider}</h4>
              <label>
                <span>API key</span>
                <input
                  type="password"
                  value={provider.api_key}
                  onChange={(event) => patchProvider(index, { api_key: event.target.value })}
                />
              </label>
              <label>
                <span>Base URL</span>
                <input
                  value={provider.base_url}
                  onChange={(event) => patchProvider(index, { base_url: event.target.value })}
                />
              </label>
              <label>
                <span>Model</span>
                <input
                  value={provider.model}
                  onChange={(event) => patchProvider(index, { model: event.target.value })}
                />
              </label>
              <label className="row">
                <input
                  type="checkbox"
                  checked={provider.enabled}
                  onChange={(event) => patchProvider(index, { enabled: event.target.checked })}
                />
                <span>Enabled</span>
              </label>
            </div>
          ))}
        </div>
        <div className="row">
          <button onClick={onClose}>Anuluj</button>
          <button
            onClick={() => {
              onSave(draft);
              onClose();
            }}
          >
            Zapisz
          </button>
        </div>
      </div>
    </div>
  );
}

