import { useEffect, useMemo, useState } from "react";
import { importCommit, importPreview } from "../api/client";
import type { Track } from "../types";

type Props = {
  open: boolean;
  onClose: () => void;
  onImported?: () => void;
};

type Step = 1 | 2 | 3 | 4;

export function ImportWizardModal({ open, onClose, onImported }: Props) {
  const [step, setStep] = useState<Step>(1);
  const [source, setSource] = useState("");
  const [scanned, setScanned] = useState<Track[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [importing, setImporting] = useState(false);
  const [report, setReport] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      setStep(1);
      setSource("");
      setScanned([]);
      setSelected([]);
      setImporting(false);
      setReport("");
      setError("");
    }
  }, [open]);

  const canNext = useMemo(() => {
    if (step === 1) return source.trim().length > 0;
    if (step === 2) return scanned.length > 0;
    if (step === 3) return selected.length > 0;
    return false;
  }, [step, source, scanned.length, selected.length]);

  if (!open) return null;

  async function next() {
    if (!canNext) return;
    if (step === 1) {
      try {
        const result = await importPreview(source);
        setScanned(result.tracks);
        setError(result.errors.join("\n"));
        setStep(2);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Nie udalo sie przeskanowac folderu.");
      }
      return;
    }
    if (step === 2) {
      setSelected(scanned.map((track) => track.path ?? "").filter(Boolean));
      setStep(3);
      return;
    }
    if (step === 3) {
      setImporting(true);
      setStep(4);
      try {
        const result = await importCommit(selected);
        setImporting(false);
        setReport(`Zaimportowano: ${result.imported}, bledy: ${result.errors.length}`);
        setError(result.errors.join("\n"));
        onImported?.();
      } catch (err) {
        setImporting(false);
        setReport("");
        setError(err instanceof Error ? err.message : "Import nie powiodl sie.");
      }
    }
  }

  function cancelImport() {
    setImporting(false);
    setReport("Import anulowany przez uzytkownika.");
  }

  return (
    <div className="modal">
      <div className="card">
        <h3>Import Wizard (krok {step}/4)</h3>
        {step === 1 ? (
          <input
            placeholder="Sciezka folderu"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          />
        ) : null}
        {step === 2 ? <pre>{scanned.map((track) => track.path ?? "").join("\n")}</pre> : null}
        {step === 3 ? <pre>{selected.join("\n")}</pre> : null}
        {step === 4 ? <div>{importing ? "Import w toku..." : report}</div> : null}
        {error ? <div className="error">{error}</div> : null}
        <div className="row">
          <button onClick={onClose}>Zamknij</button>
          {importing ? <button onClick={cancelImport}>Anuluj</button> : null}
          {!importing && step < 4 ? (
            <button onClick={() => void next()} disabled={!canNext}>
              Dalej
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
