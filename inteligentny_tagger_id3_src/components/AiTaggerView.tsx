import React, { useState, useMemo } from 'react';
import { AudioFile, ProcessingState } from '../types';
import { AIProvider, ApiKeys } from '../services/aiService';

interface AiTaggerViewProps {
  files: AudioFile[];
  aiProvider: AIProvider;
  apiKeys: ApiKeys;
  isBatchAnalyzing: boolean;
  onAiProvider: (p: AIProvider) => void;
  onProcessFile: (file: AudioFile) => void;
  onBatchAnalyze: (files: AudioFile[]) => void;
  onBatchAnalyzeAll: () => void;
  onEditFile: (id: string) => void;
  onSelectionChange: (id: string, selected: boolean) => void;
}

const providers: { id: AIProvider; label: string; color: string }[] = [
  { id: 'gemini', label: 'Gemini', color: '#00d4ff' },
  { id: 'openai', label: 'OpenAI', color: '#4ade80' },
  { id: 'grok', label: 'Grok', color: '#ec4899' },
];

const stateColors: Record<ProcessingState, string> = {
  [ProcessingState.PENDING]: '#94a3b8',
  [ProcessingState.PROCESSING]: '#00d4ff',
  [ProcessingState.DOWNLOADING]: '#8b5cf6',
  [ProcessingState.SUCCESS]: '#4ade80',
  [ProcessingState.ERROR]: '#ec4899',
};

const stateLabels: Record<ProcessingState, string> = {
  [ProcessingState.PENDING]: 'Oczekuje',
  [ProcessingState.PROCESSING]: 'Przetwarzanie...',
  [ProcessingState.DOWNLOADING]: 'Pobieranie...',
  [ProcessingState.SUCCESS]: 'Otagowano',
  [ProcessingState.ERROR]: 'Błąd',
};

const AiTaggerView: React.FC<AiTaggerViewProps> = ({
  files, aiProvider, isBatchAnalyzing,
  onAiProvider, onProcessFile, onBatchAnalyze, onBatchAnalyzeAll, onEditFile, onSelectionChange,
}) => {
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);

  const selectedFile = files.find(f => f.id === selectedFileId) || null;
  const selectedFiles = useMemo(() => files.filter(f => f.isSelected), [files]);

  const stats = useMemo(() => ({
    total: files.length,
    pending: files.filter(f => f.state === ProcessingState.PENDING).length,
    processing: files.filter(f => f.state === ProcessingState.PROCESSING).length,
    success: files.filter(f => f.state === ProcessingState.SUCCESS).length,
    error: files.filter(f => f.state === ProcessingState.ERROR).length,
  }), [files]);

  const progress = stats.total > 0 ? ((stats.success + stats.error) / stats.total) * 100 : 0;

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', gap: 20 }}>
      {/* Left: file list */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Controls */}
        <div style={{
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: 12, padding: 16, marginBottom: 16,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            {/* Provider */}
            <div style={{ display: 'flex', gap: 6 }}>
              {providers.map(p => (
                <button key={p.id} onClick={() => onAiProvider(p.id)}
                  style={{
                    padding: '6px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                    background: aiProvider === p.id ? `rgba(${p.color === '#00d4ff' ? '0,212,255' : p.color === '#4ade80' ? '74,222,128' : '236,72,153'},0.15)` : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${aiProvider === p.id ? p.color : 'rgba(255,255,255,0.08)'}`,
                    color: aiProvider === p.id ? p.color : '#94a3b8',
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}>
                  {p.label}
                </button>
              ))}
            </div>

            <div style={{ flex: 1 }} />

            <button
              onClick={() => onBatchAnalyze(selectedFiles.length > 0 ? selectedFiles : files.filter(f => f.state === ProcessingState.PENDING))}
              disabled={isBatchAnalyzing}
              className="btn-secondary"
              style={{ padding: '7px 14px', borderRadius: 6, fontSize: 12 }}
            >
              {isBatchAnalyzing ? <span className="btn-spinner" /> : null}
              {selectedFiles.length > 0 ? `Taguj zaznaczone (${selectedFiles.length})` : 'Taguj oczekujące'}
            </button>

            <button onClick={onBatchAnalyzeAll} disabled={isBatchAnalyzing}
              className="btn-cta" style={{ padding: '7px 14px', borderRadius: 6, fontSize: 12, fontWeight: 600 }}>
              Taguj wszystkie
            </button>
          </div>

          {/* Progress bar */}
          {stats.total > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 11, color: '#94a3b8' }}>
                  {stats.success + stats.error} / {stats.total} przetworzono
                </span>
                <span style={{ fontSize: 11, color: '#00d4ff' }}>{Math.round(progress)}%</span>
              </div>
              <div className="progress-track" style={{ height: 6 }}>
                <div className="progress-fill" style={{ height: '100%', width: `${progress}%` }} />
              </div>
              <div style={{ display: 'flex', gap: 16, marginTop: 6 }}>
                {[
                  { label: 'Oczekuje', count: stats.pending, color: '#94a3b8' },
                  { label: 'Przetwarza', count: stats.processing, color: '#00d4ff' },
                  { label: 'Sukces', count: stats.success, color: '#4ade80' },
                  { label: 'Błąd', count: stats.error, color: '#ec4899' },
                ].map(s => (
                  <span key={s.label} style={{ fontSize: 11, color: s.color }}>
                    {s.label}: {s.count}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* File list */}
        <div style={{
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.1)',
          borderRadius: 12, overflow: 'hidden', maxHeight: 'calc(100vh - 320px)', overflowY: 'auto',
        }}>
          {files.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
              Brak plików. Zaimportuj pliki w sekcji Import.
            </div>
          ) : files.map(file => {
            const tags = file.fetchedTags || file.originalTags;
            const isSelected = file.id === selectedFileId;
            return (
              <div
                key={file.id}
                onClick={() => setSelectedFileId(isSelected ? null : file.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '10px 14px',
                  borderBottom: '1px solid rgba(255,255,255,0.03)',
                  background: isSelected ? 'rgba(0,212,255,0.06)' : 'transparent',
                  cursor: 'pointer', transition: 'background 0.1s',
                }}
              >
                <input type="checkbox" checked={!!file.isSelected}
                  onChange={e => { e.stopPropagation(); onSelectionChange(file.id, e.target.checked); }}
                  style={{ accentColor: '#00d4ff' }} onClick={e => e.stopPropagation()} />

                <div style={{
                  width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                  background: stateColors[file.state],
                  boxShadow: file.state === ProcessingState.PROCESSING ? `0 0 6px ${stateColors[file.state]}` : 'none',
                }} />

                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <div style={{ fontSize: 13, color: '#e6f7ff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {tags?.title || file.file.name}
                  </div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>
                    {tags?.artist || 'Nieznany artysta'}
                  </div>
                </div>

                <span className={`badge badge-${file.state.toLowerCase()}`} style={{
                  background: `${stateColors[file.state]}22`,
                  color: stateColors[file.state], padding: '2px 8px', borderRadius: 10, fontSize: 10, flexShrink: 0,
                }}>
                  {stateLabels[file.state]}
                </span>

                {(file.state === ProcessingState.PENDING || file.state === ProcessingState.ERROR) && (
                  <button
                    onClick={e => { e.stopPropagation(); onProcessFile(file); }}
                    style={{ padding: '4px 10px', borderRadius: 5, background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)', color: '#8b5cf6', cursor: 'pointer', fontSize: 11, flexShrink: 0 }}
                  >AI</button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Right: tag comparison */}
      {selectedFile && (
        <div style={{ width: 300, flexShrink: 0 }}>
          <div style={{
            background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
            borderRadius: 12, padding: 16,
          }}>
            <h4 style={{ color: '#e6f7ff', fontSize: 13, fontWeight: 600, margin: '0 0 14px' }}>Porównanie tagów</h4>

            {[
              { label: 'Tytuł', origKey: 'title', fetchedKey: 'title' },
              { label: 'Artysta', origKey: 'artist', fetchedKey: 'artist' },
              { label: 'Album', origKey: 'album', fetchedKey: 'album' },
              { label: 'Rok', origKey: 'year', fetchedKey: 'year' },
              { label: 'Gatunek', origKey: 'genre', fetchedKey: 'genre' },
              { label: 'BPM', origKey: 'bpm', fetchedKey: 'bpm' },
              { label: 'Tonacja', origKey: 'key', fetchedKey: 'key' },
            ].map(row => {
              const orig = (selectedFile.originalTags as any)[row.origKey];
              const fetched = selectedFile.fetchedTags ? (selectedFile.fetchedTags as any)[row.fetchedKey] : null;
              const hasChange = fetched && String(fetched) !== String(orig || '');
              return (
                <div key={row.label} style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 10, color: '#64748b', marginBottom: 3 }}>{row.label}</div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <div style={{ flex: 1, padding: '5px 8px', borderRadius: 5, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', fontSize: 11, color: '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {orig?.toString() || '—'}
                    </div>
                    {selectedFile.fetchedTags && (
                      <div style={{ flex: 1, padding: '5px 8px', borderRadius: 5, background: hasChange ? 'rgba(74,222,128,0.08)' : 'rgba(255,255,255,0.03)', border: `1px solid ${hasChange ? 'rgba(74,222,128,0.3)' : 'rgba(255,255,255,0.06)'}`, fontSize: 11, color: hasChange ? '#4ade80' : '#94a3b8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {fetched?.toString() || '—'}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button onClick={() => onEditFile(selectedFile.id)} className="btn-secondary"
                style={{ flex: 1, padding: '8px', borderRadius: 6, fontSize: 12 }}>
                Edytuj ręcznie
              </button>
              {(selectedFile.state === ProcessingState.PENDING || selectedFile.state === ProcessingState.ERROR) && (
                <button onClick={() => onProcessFile(selectedFile)} className="btn-cta"
                  style={{ flex: 1, padding: '8px', borderRadius: 6, fontSize: 12, fontWeight: 600 }}>
                  Taguj AI
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AiTaggerView;
