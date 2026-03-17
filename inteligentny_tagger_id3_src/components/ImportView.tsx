import React, { useState, useRef, useCallback } from 'react';
import { ViewType } from '../types';

interface ImportViewProps {
  onFilesSelected: (files: FileList) => void;
  onDirectoryConnect: (handle: any) => void;
  onDirectoryPicker: () => void;
  onUrlSubmitted: (url: string) => void;
  isProcessing: boolean;
  onNavigate: (view: ViewType) => void;
}

type WizardStep = 1 | 2 | 3;

interface PendingFileInfo {
  name: string;
  size: number;
  type: string;
}

const ImportView: React.FC<ImportViewProps> = ({
  onFilesSelected, onDirectoryConnect, onDirectoryPicker, onUrlSubmitted, isProcessing, onNavigate,
}) => {
  const [step, setStep] = useState<WizardStep>(1);
  const [isDragging, setIsDragging] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<PendingFileInfo[]>([]);
  const [pendingFileList, setPendingFileList] = useState<FileList | null>(null);
  const [progress, setProgress] = useState<Map<string, number>>(new Map());
  const [importDone, setImportDone] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dirInputRef = useRef<HTMLInputElement>(null);

  const SUPPORTED_FORMATS = ['audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/flac', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/x-m4a', 'audio/aac', 'audio/x-ms-wma'];

  const handleFiles = useCallback((fileList: FileList) => {
    const valid = Array.from(fileList).filter(f => SUPPORTED_FORMATS.includes(f.type));
    if (valid.length === 0) return;
    setPendingFiles(valid.map(f => ({ name: f.name, size: f.size, type: f.type })));
    setPendingFileList(fileList);
    setStep(2);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const startImport = async () => {
    if (!pendingFileList) return;
    setStep(3);
    setImportDone(false);
    const initMap = new Map<string, number>();
    pendingFiles.forEach(f => initMap.set(f.name, 0));
    setProgress(initMap);

    // Simulate progress per file then call real import
    for (let i = 0; i < pendingFiles.length; i++) {
      const fname = pendingFiles[i].name;
      for (let p = 10; p <= 90; p += 20) {
        await new Promise(r => setTimeout(r, 30));
        setProgress(prev => new Map(prev).set(fname, p));
      }
    }

    onFilesSelected(pendingFileList);

    // Finalize progress
    setProgress(prev => {
      const next = new Map(prev);
      pendingFiles.forEach(f => next.set(f.name, 100));
      return next;
    });
    setImportDone(true);
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const steps = ['Wybór folderu', 'Analiza plików', 'Importowanie'];

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      {/* Step indicator */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 28 }}>
        {steps.map((label, i) => {
          const n = (i + 1) as WizardStep;
          const isActive = step === n;
          const isDone = step > n;
          return (
            <React.Fragment key={n}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700,
                  background: isDone ? '#00d4ff' : isActive ? 'rgba(0,212,255,0.2)' : 'rgba(255,255,255,0.06)',
                  border: `2px solid ${isDone || isActive ? '#00d4ff' : 'rgba(255,255,255,0.1)'}`,
                  color: isDone ? '#0a0d1a' : isActive ? '#00d4ff' : '#64748b',
                }}>
                  {isDone ? '✓' : n}
                </div>
                <span style={{ fontSize: 13, color: isActive ? '#e6f7ff' : '#64748b', fontWeight: isActive ? 600 : 400 }}>{label}</span>
              </div>
              {i < steps.length - 1 && (
                <div style={{ flex: 1, height: 2, background: step > n ? '#00d4ff' : 'rgba(255,255,255,0.06)', margin: '0 12px' }} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: 20 }}>
        {/* Main content */}
        <div style={{
          flex: 1,
          background: 'rgba(13,17,42,0.85)',
          border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: 16, padding: 28,
          backdropFilter: 'blur(12px)',
        }}>
          <h2 style={{ color: '#e6f7ff', fontSize: 18, fontWeight: 600, margin: '0 0 20px' }}>
            {steps[step - 1]}
          </h2>

          {step === 1 && (
            <>
              {/* Drag & Drop zone */}
              <div
                onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                className={isDragging ? 'drag-active' : ''}
                style={{
                  border: `2px dashed ${isDragging ? '#00d4ff' : 'rgba(0,212,255,0.25)'}`,
                  borderRadius: 12, padding: '48px 24px',
                  textAlign: 'center', cursor: 'pointer',
                  background: isDragging ? 'rgba(0,212,255,0.05)' : 'rgba(255,255,255,0.02)',
                  transition: 'all 0.2s', marginBottom: 16,
                }}
                onClick={() => fileInputRef.current?.click()}
              >
                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" strokeWidth="1.2" style={{ marginBottom: 14, opacity: isDragging ? 1 : 0.6 }}>
                  <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
                  <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3"/>
                </svg>
                <p style={{ color: '#e6f7ff', fontSize: 15, margin: '0 0 8px', fontWeight: 500 }}>
                  Przeciągnij tutaj pliki lub folder
                </p>
                <p style={{ color: '#64748b', fontSize: 12, margin: 0 }}>
                  MP3, M4A, FLAC, WAV, OGG, AAC i inne
                </p>
              </div>

              <input ref={fileInputRef} type="file" multiple accept="audio/*" style={{ display: 'none' }}
                onChange={e => e.target.files && handleFiles(e.target.files)} />
              <input ref={dirInputRef} type="file" multiple accept="audio/*" style={{ display: 'none' }}
                // @ts-ignore
                webkitdirectory=""
                onChange={e => e.target.files && handleFiles(e.target.files)} />

              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  onClick={() => dirInputRef.current?.click()}
                  className="btn-cta"
                  style={{ flex: 1, padding: '12px 16px', borderRadius: 8, fontSize: 14, fontWeight: 600 }}
                >
                  Wybierz folder
                </button>
                {'showDirectoryPicker' in window && (
                  <button
                    onClick={onDirectoryPicker}
                    className="btn-secondary"
                    style={{ flex: 1, padding: '12px 16px', borderRadius: 8, fontSize: 14 }}
                  >
                    Folder z dostępem
                  </button>
                )}
              </div>
            </>
          )}

          {step === 2 && (
            <>
              <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 16 }}>
                Znaleziono {pendingFiles.length} plików audio. Gotowy do importu.
              </p>
              <div style={{ maxHeight: 300, overflowY: 'auto', marginBottom: 20 }}>
                {pendingFiles.slice(0, 50).map((f, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 10px', borderRadius: 6,
                    background: i % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
                  }}>
                    <span style={{ fontSize: 12, color: '#cbd5e1', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '75%' }}>
                      {f.name}
                    </span>
                    <span style={{ fontSize: 11, color: '#64748b', flexShrink: 0 }}>{formatBytes(f.size)}</span>
                  </div>
                ))}
                {pendingFiles.length > 50 && (
                  <p style={{ color: '#64748b', fontSize: 12, textAlign: 'center', marginTop: 8 }}>
                    ... i {pendingFiles.length - 50} więcej
                  </p>
                )}
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={() => setStep(1)} className="btn-secondary"
                  style={{ padding: '10px 20px', borderRadius: 8, fontSize: 13 }}>
                  Wstecz
                </button>
                <button onClick={startImport} className="btn-cta"
                  style={{ flex: 1, padding: '10px 20px', borderRadius: 8, fontSize: 14, fontWeight: 600 }}>
                  Importuj {pendingFiles.length} plików
                </button>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 20 }}>
                {importDone ? 'Import zakończony pomyślnie!' : 'Importowanie plików...'}
              </p>
              {importDone && (
                <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                  <button onClick={() => onNavigate('library')} className="btn-cta"
                    style={{ flex: 1, padding: '10px 20px', borderRadius: 8, fontSize: 14, fontWeight: 600 }}>
                    Przejdź do Biblioteki
                  </button>
                  <button onClick={() => { setStep(1); setPendingFiles([]); setProgress(new Map()); setImportDone(false); }}
                    className="btn-secondary"
                    style={{ padding: '10px 16px', borderRadius: 8, fontSize: 13 }}>
                    Importuj więcej
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Progress panel */}
        {step === 3 && (
          <div style={{
            width: 260, flexShrink: 0,
            background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(139,92,246,0.2)',
            borderRadius: 16, padding: 20,
          }}>
            <h3 style={{ color: '#e6f7ff', fontSize: 14, fontWeight: 600, margin: '0 0 16px' }}>
              Postęp
            </h3>
            <div style={{ maxHeight: 'calc(100vh - 300px)', overflowY: 'auto' }}>
              {pendingFiles.map(f => {
                const pct = progress.get(f.name) || 0;
                return (
                  <div key={f.name} style={{ marginBottom: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 11, color: '#cbd5e1', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '75%', whiteSpace: 'nowrap' }}>
                        {f.name}
                      </span>
                      <span style={{ fontSize: 11, color: '#00d4ff', flexShrink: 0 }}>{pct}%</span>
                    </div>
                    <div className="progress-track" style={{ height: 6 }}>
                      <div
                        className={`progress-fill${pct < 100 ? ' progress-bar-active' : ''}`}
                        style={{ height: '100%', width: `${pct}%` }}
                      />
                    </div>
                    {pct === 100 && (
                      <div style={{ fontSize: 10, color: '#4ade80', marginTop: 2 }}>✓ Zaimportowano</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImportView;
