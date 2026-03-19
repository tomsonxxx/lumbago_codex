import { useMemo, useState } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
};

type Step = 1 | 2 | 3 | 4;

export function ImportWizardModal({ open, onClose }: Props) {
  const [step, setStep] = useState<Step>(1);
  const [source, setSource] = useState("");
  const [scanned, setScanned] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [importing, setImporting] = useState(false);
  const [report, setReport] = useState("");

  const canNext = useMemo(() => {
    if (step === 1) return source.trim().length > 0;
    if (step === 2) return scanned.length > 0;
    if (step === 3) return selected.length > 0;
    return false;
  }, [step, source, scanned.length, selected.length]);

  if (!open) return null;

  function next() {
    if (!canNext) return;
    if (step === 1) {
      setScanned([`${source}/track_1.mp3`, `${source}/track_2.mp3`]);
      setStep(2);
      return;
    }
    if (step === 2) {
      setSelected(scanned);
      setStep(3);
      return;
    }
    if (step === 3) {
      setImporting(true);
      setStep(4);
      setTimeout(() => {
        setImporting(false);
        setReport(`Zaimportowano: ${selected.length}, bledy: 0`);
      }, 400);
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
        {step === 2 ? <pre>{scanned.join("\n")}</pre> : null}
        {step === 3 ? <pre>{selected.join("\n")}</pre> : null}
        {step === 4 ? <div>{importing ? "Import w toku..." : report}</div> : null}
        <div className="row">
          <button onClick={onClose}>Zamknij</button>
          {importing ? <button onClick={cancelImport}>Anuluj</button> : null}
          {!importing && step < 4 ? (
            <button onClick={next} disabled={!canNext}>
              Dalej
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

