import React, { useState, useMemo, useCallback } from 'react';
import { AudioFile, ProcessingState, LibraryFilters } from '../types';
import { SortKey } from '../utils/sortingUtils';
import { formatDuration } from '../utils/audioUtils';

interface LibraryViewProps {
  files: AudioFile[];
  sortKey: SortKey;
  sortDirection: 'asc' | 'desc';
  onSortChange: (key: SortKey, dir: 'asc' | 'desc') => void;
  globalSearch: string;
  onEditFile: (id: string) => void;
  onDeleteFile: (id: string) => void;
  onProcessFile: (file: AudioFile) => void;
  onSelectionChange: (id: string, selected: boolean) => void;
  onToggleSelectAll: () => void;
  allFilesSelected: boolean;
  selectedFiles: AudioFile[];
  onBatchAnalyze: (files: AudioFile[]) => void;
  onBatchAnalyzeAll: () => void;
  onDownloadOrSave: () => void;
  onBatchEdit: () => void;
  onExportCsv: () => void;
  onDeleteSelected: () => void;
  onClearAll: () => void;
  onRenamePattern: () => void;
  isBatchAnalyzing: boolean;
  isSaving: boolean;
  directoryHandle: any;
  isRestored: boolean;
  onSetPlayer: (id: string) => void;
  onRatingChange: (id: string, rating: number) => void;
}

const StatusDot: React.FC<{ state: ProcessingState }> = ({ state }) => {
  const colors: Record<ProcessingState, string> = {
    [ProcessingState.PENDING]: '#94a3b8',
    [ProcessingState.PROCESSING]: '#00d4ff',
    [ProcessingState.DOWNLOADING]: '#8b5cf6',
    [ProcessingState.SUCCESS]: '#4ade80',
    [ProcessingState.ERROR]: '#ec4899',
  };
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
      background: colors[state],
      boxShadow: state === ProcessingState.PROCESSING ? `0 0 6px ${colors[state]}` : 'none',
    }} />
  );
};

const StarRating: React.FC<{ rating?: number; onRate: (r: number) => void }> = ({ rating = 0, onRate }) => {
  const [hover, setHover] = useState(0);
  return (
    <span style={{ display: 'inline-flex', gap: 2 }}>
      {[1,2,3,4,5].map(n => (
        <span
          key={n}
          className="star-btn"
          onClick={e => { e.stopPropagation(); onRate(n); }}
          onMouseEnter={() => setHover(n)}
          onMouseLeave={() => setHover(0)}
          style={{ color: n <= (hover || rating) ? '#fbbf24' : '#374151', fontSize: 14 }}
        >★</span>
      ))}
    </span>
  );
};

const MUSIC_KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',
  'Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm'];

const LibraryView: React.FC<LibraryViewProps> = ({
  files, sortKey, sortDirection, onSortChange, globalSearch,
  onEditFile, onDeleteFile, onProcessFile, onSelectionChange,
  onToggleSelectAll, allFilesSelected, selectedFiles,
  onBatchAnalyze, onBatchAnalyzeAll, onDownloadOrSave, onBatchEdit,
  onExportCsv, onDeleteSelected, onClearAll, onRenamePattern,
  isBatchAnalyzing, isSaving, directoryHandle, isRestored, onSetPlayer, onRatingChange,
}) => {
  const [filters, setFilters] = useState<LibraryFilters>({
    genre: null, status: null, bpmMin: null, bpmMax: null, key: null, rating: null,
  });
  const [showFilters, setShowFilters] = useState(true);
  const [activeChips, setActiveChips] = useState<Set<string>>(new Set());

  const uniqueGenres = useMemo(() => {
    const genres = new Set<string>();
    files.forEach(f => { const g = (f.fetchedTags || f.originalTags)?.genre; if (g) genres.add(g); });
    return Array.from(genres).sort();
  }, [files]);

  const toggleChip = useCallback((chip: string) => {
    setActiveChips(prev => {
      const next = new Set(prev);
      if (next.has(chip)) { next.delete(chip); }
      else { next.add(chip); }
      return next;
    });
  }, []);

  const filteredFiles = useMemo(() => {
    let result = [...files];

    // Global search
    if (globalSearch) {
      const q = globalSearch.toLowerCase();
      result = result.filter(f => {
        const t = f.fetchedTags || f.originalTags;
        return (f.file.name.toLowerCase().includes(q) ||
          t.title?.toLowerCase().includes(q) ||
          t.artist?.toLowerCase().includes(q) ||
          t.album?.toLowerCase().includes(q));
      });
    }

    // Chip filters
    for (const chip of activeChips) {
      const bpmMatch = chip.match(/^(\d+)-(\d+)\s*BPM$/i);
      if (bpmMatch) {
        const lo = parseInt(bpmMatch[1]), hi = parseInt(bpmMatch[2]);
        result = result.filter(f => { const bpm = (f.fetchedTags || f.originalTags)?.bpm; return bpm !== undefined && bpm >= lo && bpm <= hi; });
      } else {
        result = result.filter(f => {
          const t = f.fetchedTags || f.originalTags;
          return t.genre?.toLowerCase() === chip.toLowerCase() || t.key?.toLowerCase() === chip.toLowerCase();
        });
      }
    }

    // Sidebar filters
    if (filters.genre) result = result.filter(f => (f.fetchedTags || f.originalTags)?.genre === filters.genre);
    if (filters.status) result = result.filter(f => f.state === filters.status);
    if (filters.bpmMin !== null) result = result.filter(f => { const bpm = (f.fetchedTags || f.originalTags)?.bpm; return bpm !== undefined && bpm >= (filters.bpmMin ?? 0); });
    if (filters.bpmMax !== null) result = result.filter(f => { const bpm = (f.fetchedTags || f.originalTags)?.bpm; return bpm !== undefined && bpm <= (filters.bpmMax ?? 999); });
    if (filters.key) result = result.filter(f => (f.fetchedTags || f.originalTags)?.key === filters.key);
    if (filters.rating !== null) result = result.filter(f => (f.rating || 0) >= (filters.rating ?? 1));

    return result;
  }, [files, globalSearch, activeChips, filters]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) onSortChange(key, sortDirection === 'asc' ? 'desc' : 'asc');
    else onSortChange(key, 'asc');
  };

  const SortHeader: React.FC<{ label: string; colKey: SortKey }> = ({ label, colKey }) => (
    <th
      onClick={() => handleSort(colKey)}
      style={{ padding: '10px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: sortKey === colKey ? '#00d4ff' : '#64748b', cursor: 'pointer', whiteSpace: 'nowrap', userSelect: 'none' }}
    >
      {label} {sortKey === colKey ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
    </th>
  );

  const quickChips = ['Pop', 'Rock', 'Elektroniczna', '120-130 BPM', 'Am', 'Em'];

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 160px)' }}>
      {/* Main table */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Toolbar */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: '#64748b', marginRight: 4 }}>
            {filteredFiles.length} / {files.length} plików
            {selectedFiles.length > 0 && ` • ${selectedFiles.length} zaznaczonych`}
          </span>
          <div style={{ flex: 1 }} />
          {selectedFiles.length > 0 && (
            <>
              <button onClick={() => onBatchAnalyze(selectedFiles)} disabled={isBatchAnalyzing}
                className="btn-secondary" style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12 }}>
                {isBatchAnalyzing ? <span className="btn-spinner" /> : null}Taguj zaznaczone
              </button>
              <button onClick={onDownloadOrSave} disabled={isSaving}
                className="btn-cta" style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12 }}>
                {directoryHandle ? 'Zapisz' : 'Pobierz ZIP'}
              </button>
              <button onClick={onBatchEdit} className="btn-secondary" style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12 }}>
                Edycja hurtowa
              </button>
              <button onClick={onDeleteSelected} style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, background: 'rgba(236,72,153,0.15)', border: '1px solid rgba(236,72,153,0.3)', color: '#ec4899', cursor: 'pointer' }}>
                Usuń zaznaczone
              </button>
            </>
          )}
          <button onClick={onBatchAnalyzeAll} disabled={isBatchAnalyzing}
            className="btn-secondary" style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12 }}>
            Taguj wszystkie
          </button>
          <button onClick={onRenamePattern} className="btn-secondary" style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12 }}>
            Szablon nazw
          </button>
          <button onClick={onExportCsv} className="btn-secondary" style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12 }}>
            CSV
          </button>
          <button onClick={() => setShowFilters(s => !s)} className="btn-secondary"
            style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, borderColor: showFilters ? '#00d4ff' : undefined }}>
            Filtry
          </button>
        </div>

        {files.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12, color: '#94a3b8' }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" opacity={0.4}>
              <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
            </svg>
            <p style={{ margin: 0, fontSize: 14 }}>Brak plików w bibliotece</p>
          </div>
        ) : (
          <div style={{ flex: 1, overflowY: 'auto', borderRadius: 12, border: '1px solid rgba(0,212,255,0.1)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ position: 'sticky', top: 0, background: '#0a0d1a', zIndex: 2 }}>
                <tr style={{ borderBottom: '1px solid rgba(0,212,255,0.1)' }}>
                  <th style={{ padding: '10px 12px', width: 32 }}>
                    <input type="checkbox" checked={allFilesSelected} onChange={onToggleSelectAll}
                      style={{ accentColor: '#00d4ff' }} />
                  </th>
                  <th style={{ padding: '10px 8px', width: 12 }}></th>
                  <SortHeader label="Tytuł" colKey="title" />
                  <SortHeader label="Artysta" colKey="artist" />
                  <SortHeader label="Album" colKey="album" />
                  <th style={{ padding: '10px 12px', fontSize: 11, fontWeight: 600, color: '#64748b' }}>BPM</th>
                  <th style={{ padding: '10px 12px', fontSize: 11, fontWeight: 600, color: '#64748b' }}>Tonacja</th>
                  <th style={{ padding: '10px 12px', fontSize: 11, fontWeight: 600, color: '#64748b' }}>Czas</th>
                  <th style={{ padding: '10px 12px', fontSize: 11, fontWeight: 600, color: '#64748b' }}>Ocena</th>
                  <th style={{ padding: '10px 12px', fontSize: 11, fontWeight: 600, color: '#64748b' }}>Akcje</th>
                </tr>
              </thead>
              <tbody>
                {filteredFiles.map(file => {
                  const tags = file.fetchedTags || file.originalTags;
                  return (
                    <tr
                      key={file.id}
                      className={`track-row${file.isSelected ? ' selected' : ''}`}
                      onDoubleClick={() => onSetPlayer(file.id)}
                      style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}
                    >
                      <td style={{ padding: '8px 12px' }}>
                        <input type="checkbox" checked={!!file.isSelected}
                          onChange={e => onSelectionChange(file.id, e.target.checked)}
                          style={{ accentColor: '#00d4ff' }}
                          onClick={e => e.stopPropagation()}
                        />
                      </td>
                      <td style={{ padding: '8px 4px' }}>
                        <StatusDot state={file.state} />
                      </td>
                      <td style={{ padding: '8px 12px', maxWidth: 180 }}>
                        <div style={{ fontSize: 13, color: '#e6f7ff', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {tags?.title || file.file.name}
                        </div>
                        {file.state === ProcessingState.ERROR && (
                          <div style={{ fontSize: 10, color: '#ec4899' }}>{file.errorMessage}</div>
                        )}
                      </td>
                      <td style={{ padding: '8px 12px', fontSize: 12, color: '#94a3b8', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {tags?.artist || '—'}
                      </td>
                      <td style={{ padding: '8px 12px', fontSize: 12, color: '#94a3b8', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {tags?.album || '—'}
                      </td>
                      <td style={{ padding: '8px 12px', fontSize: 12, color: '#00d4ff', textAlign: 'center' }}>
                        {tags?.bpm || '—'}
                      </td>
                      <td style={{ padding: '8px 12px', fontSize: 12, color: '#8b5cf6', textAlign: 'center' }}>
                        {tags?.key || '—'}
                      </td>
                      <td style={{ padding: '8px 12px', fontSize: 12, color: '#64748b', textAlign: 'center' }}>
                        {formatDuration(file.duration || 0)}
                      </td>
                      <td style={{ padding: '8px 12px' }}>
                        <StarRating rating={file.rating} onRate={r => onRatingChange(file.id, r)} />
                      </td>
                      <td style={{ padding: '8px 8px' }}>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <button
                            onClick={e => { e.stopPropagation(); onEditFile(file.id); }}
                            style={{ padding: '3px 8px', borderRadius: 4, background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.2)', color: '#00d4ff', cursor: 'pointer', fontSize: 11 }}
                          >Edytuj</button>
                          {file.state === ProcessingState.PENDING || file.state === ProcessingState.ERROR ? (
                            <button
                              onClick={e => { e.stopPropagation(); onProcessFile(file); }}
                              style={{ padding: '3px 8px', borderRadius: 4, background: 'rgba(139,92,246,0.1)', border: '1px solid rgba(139,92,246,0.2)', color: '#8b5cf6', cursor: 'pointer', fontSize: 11 }}
                            >AI</button>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Right filter panel */}
      {showFilters && (
        <div style={{
          width: 220, flexShrink: 0,
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: 12, padding: 16,
          overflowY: 'auto', alignSelf: 'flex-start',
          maxHeight: 'calc(100vh - 160px)',
        }}>
          <h4 style={{ color: '#e6f7ff', fontSize: 13, fontWeight: 600, margin: '0 0 12px' }}>Filtry</h4>

          {/* Quick chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
            {quickChips.map(chip => (
              <button key={chip} className={`filter-chip${activeChips.has(chip) ? ' active' : ''}`}
                onClick={() => toggleChip(chip)}>
                {chip}
              </button>
            ))}
          </div>

          {/* Gatunek */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 6 }}>Gatunek</label>
            <select
              value={filters.genre || ''}
              onChange={e => setFilters(f => ({ ...f, genre: e.target.value || null }))}
              className="input-dark"
              style={{ width: '100%', padding: '6px 8px', borderRadius: 6, fontSize: 12 }}
            >
              <option value="">Wszystkie</option>
              {uniqueGenres.map(g => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>

          {/* BPM Range */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 6 }}>BPM (zakres)</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input type="number" placeholder="Min" min={0} max={300}
                value={filters.bpmMin ?? ''}
                onChange={e => setFilters(f => ({ ...f, bpmMin: e.target.value ? parseInt(e.target.value) : null }))}
                className="input-dark"
                style={{ width: '50%', padding: '5px 8px', borderRadius: 6, fontSize: 12 }}
              />
              <input type="number" placeholder="Max" min={0} max={300}
                value={filters.bpmMax ?? ''}
                onChange={e => setFilters(f => ({ ...f, bpmMax: e.target.value ? parseInt(e.target.value) : null }))}
                className="input-dark"
                style={{ width: '50%', padding: '5px 8px', borderRadius: 6, fontSize: 12 }}
              />
            </div>
          </div>

          {/* Tonacja */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 6 }}>Tonacja</label>
            <select
              value={filters.key || ''}
              onChange={e => setFilters(f => ({ ...f, key: e.target.value || null }))}
              className="input-dark"
              style={{ width: '100%', padding: '6px 8px', borderRadius: 6, fontSize: 12 }}
            >
              <option value="">Wszystkie</option>
              {MUSIC_KEYS.map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>

          {/* Ocena */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 6 }}>Ocena (min)</label>
            <select
              value={filters.rating ?? ''}
              onChange={e => setFilters(f => ({ ...f, rating: e.target.value ? parseInt(e.target.value) : null }))}
              className="input-dark"
              style={{ width: '100%', padding: '6px 8px', borderRadius: 6, fontSize: 12 }}
            >
              <option value="">Dowolna</option>
              <option value="1">★+</option>
              <option value="2">★★+</option>
              <option value="3">★★★+</option>
              <option value="4">★★★★+</option>
              <option value="5">★★★★★</option>
            </select>
          </div>

          {/* Status */}
          <div style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 6 }}>Status</label>
            <select
              value={filters.status || ''}
              onChange={e => setFilters(f => ({ ...f, status: e.target.value as ProcessingState || null }))}
              className="input-dark"
              style={{ width: '100%', padding: '6px 8px', borderRadius: 6, fontSize: 12 }}
            >
              <option value="">Wszystkie</option>
              <option value={ProcessingState.PENDING}>Oczekujące</option>
              <option value={ProcessingState.SUCCESS}>Przetworzone</option>
              <option value={ProcessingState.ERROR}>Błędy</option>
            </select>
          </div>

          <button
            onClick={() => { setFilters({ genre: null, status: null, bpmMin: null, bpmMax: null, key: null, rating: null }); setActiveChips(new Set()); }}
            style={{ width: '100%', padding: '7px', borderRadius: 6, background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', cursor: 'pointer', fontSize: 12 }}
          >
            Wyczyść filtry
          </button>
        </div>
      )}
    </div>
  );
};

export default LibraryView;
