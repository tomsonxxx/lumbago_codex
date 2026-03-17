import React, { useState, useMemo } from 'react';
import { AudioFile, DuplicateGroup } from '../types';

interface DuplicatesViewProps {
  files: AudioFile[];
  onDeleteFiles: (ids: string[]) => void;
  onUpdateFiles: (updates: Partial<AudioFile>[]) => void;
}

const normalize = (s?: string) => s?.toLowerCase().trim().replace(/\s+/g, ' ') ?? '';

const DuplicatesView: React.FC<DuplicatesViewProps> = ({ files, onDeleteFiles, onUpdateFiles }) => {
  const [analyzed, setAnalyzed] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);

  const duplicateGroups = useMemo((): DuplicateGroup[] => {
    if (!analyzed) return [];
    const groups: DuplicateGroup[] = [];
    const processed = new Set<string>();

    files.forEach(fileA => {
      if (processed.has(fileA.id)) return;
      const group: string[] = [fileA.id];
      const tagsA = fileA.fetchedTags || fileA.originalTags;

      files.forEach(fileB => {
        if (fileA.id === fileB.id || processed.has(fileB.id)) return;
        const tagsB = fileB.fetchedTags || fileB.originalTags;

        const titleMatch = normalize(tagsA.title) === normalize(tagsB.title) && normalize(tagsA.title) !== '';
        const artistMatch = normalize(tagsA.artist) === normalize(tagsB.artist) && normalize(tagsA.artist) !== '';
        const filenameMatch = normalize(fileA.file.name) === normalize(fileB.file.name) && normalize(fileA.file.name) !== '';

        if ((titleMatch && artistMatch) || filenameMatch) {
          group.push(fileB.id);
          processed.add(fileB.id);
        }
      });

      if (group.length > 1) {
        processed.add(fileA.id);
        const confidence: DuplicateGroup['confidence'] =
          group.length > 3 ? 'very_high' : group.length === 3 ? 'high' : 'medium';
        groups.push({ id: `grp-${fileA.id}`, confidence, fileIds: group });
      }
    });

    return groups;
  }, [files, analyzed]);

  const confLabel: Record<DuplicateGroup['confidence'], string> = {
    very_high: 'Bardzo wysoka zgodność',
    high: 'Wysoka zgodność',
    medium: 'Średnia zgodność',
  };
  const confClass: Record<DuplicateGroup['confidence'], string> = {
    very_high: 'conf-very-high',
    high: 'conf-high',
    medium: 'conf-medium',
  };

  const keepFirst = (group: DuplicateGroup) => {
    const toDelete = group.fileIds.slice(1);
    onDeleteFiles(toDelete);
    setSelectedGroupId(null);
  };

  const deleteAll = (group: DuplicateGroup) => {
    onDeleteFiles(group.fileIds);
    setSelectedGroupId(null);
  };

  const mergeGroup = (group: DuplicateGroup) => {
    const groupFiles = group.fileIds.map(id => files.find(f => f.id === id)).filter(Boolean) as AudioFile[];
    if (groupFiles.length < 2) return;
    // Merge: pick best non-empty values from all files
    const merged = { ...groupFiles[0].originalTags };
    groupFiles.forEach(f => {
      const t = f.fetchedTags || f.originalTags;
      Object.keys(t).forEach(k => {
        const key = k as keyof typeof t;
        if (!merged[key] && t[key]) (merged as any)[key] = t[key];
      });
    });
    // Apply merged tags to first file, delete rest
    const updates = [{ id: groupFiles[0].id, fetchedTags: merged }];
    onUpdateFiles(updates);
    onDeleteFiles(group.fileIds.slice(1));
    setSelectedGroupId(null);
  };

  const selectedGroup = duplicateGroups.find(g => g.id === selectedGroupId);

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
        <h2 style={{ color: '#e6f7ff', fontSize: 18, fontWeight: 600, margin: 0 }}>Zduplikowane pliki</h2>
        {!analyzed && (
          <button
            onClick={() => setAnalyzed(true)}
            className="btn-cta"
            style={{ padding: '8px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600 }}
          >
            Analizuj duplikaty
          </button>
        )}
        {analyzed && (
          <span style={{ fontSize: 13, color: '#94a3b8' }}>
            Znaleziono {duplicateGroups.length} grup duplikatów
          </span>
        )}
        {analyzed && (
          <button onClick={() => { setAnalyzed(false); setSelectedGroupId(null); }}
            className="btn-secondary" style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12 }}>
            Resetuj
          </button>
        )}
      </div>

      {!analyzed && (
        <div style={{
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: 16, padding: 40, textAlign: 'center',
        }}>
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" strokeWidth="1.2" style={{ opacity: 0.5, marginBottom: 16 }}>
            <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
          </svg>
          <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 20 }}>
            Kliknij "Analizuj duplikaty" aby wyszukać zduplikowane pliki w bibliotece.
          </p>
          <p style={{ color: '#64748b', fontSize: 12 }}>
            Analiza porównuje tytuł + artysta oraz nazwy plików.
          </p>
        </div>
      )}

      {analyzed && duplicateGroups.length === 0 && (
        <div style={{
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(74,222,128,0.2)',
          borderRadius: 16, padding: 40, textAlign: 'center',
        }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>✓</div>
          <p style={{ color: '#4ade80', fontSize: 15, fontWeight: 600, margin: '0 0 8px' }}>Brak duplikatów!</p>
          <p style={{ color: '#94a3b8', fontSize: 13 }}>Wszystkie pliki w bibliotece są unikalne.</p>
        </div>
      )}

      {analyzed && duplicateGroups.length > 0 && (
        <div style={{ display: 'flex', gap: 16 }}>
          {/* Groups list */}
          <div style={{ flex: 1 }}>
            {duplicateGroups.map((group, gIdx) => {
              const groupFiles = group.fileIds.map(id => files.find(f => f.id === id)).filter(Boolean) as AudioFile[];
              const isSelected = selectedGroupId === group.id;
              return (
                <div
                  key={group.id}
                  onClick={() => setSelectedGroupId(isSelected ? null : group.id)}
                  style={{
                    background: isSelected ? 'rgba(0,212,255,0.05)' : 'rgba(13,17,42,0.85)',
                    border: `1px solid ${isSelected ? 'rgba(0,212,255,0.4)' : 'rgba(0,212,255,0.12)'}`,
                    borderRadius: 12, padding: 16, marginBottom: 12,
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                    <span style={{ fontWeight: 700, color: '#94a3b8', fontSize: 13 }}>Grupa {gIdx + 1}</span>
                    <span className={`badge ${confClass[group.confidence]}`}>
                      {confLabel[group.confidence]}
                    </span>
                    <span style={{ marginLeft: 'auto', fontSize: 12, color: '#64748b' }}>
                      {group.fileIds.length} pliki
                    </span>
                  </div>

                  {/* File thumbnails */}
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    {groupFiles.map(f => {
                      const cover = (f.fetchedTags || f.originalTags)?.albumCoverUrl;
                      const title = (f.fetchedTags || f.originalTags)?.title || f.file.name;
                      return (
                        <div key={f.id} style={{ textAlign: 'center' }}>
                          <div style={{
                            width: 52, height: 52, borderRadius: 8,
                            background: 'linear-gradient(135deg, rgba(0,212,255,0.15), rgba(139,92,246,0.15))',
                            border: '1px solid rgba(0,212,255,0.15)',
                            overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}>
                            {cover ? (
                              <img src={cover} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            ) : (
                              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" strokeWidth="1.5" opacity={0.5}>
                                <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/>
                              </svg>
                            )}
                          </div>
                          <div style={{ fontSize: 9, color: '#64748b', marginTop: 4, maxWidth: 52, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {title}
                          </div>
                        </div>
                      );
                    })}

                    <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                      <button onClick={e => { e.stopPropagation(); keepFirst(group); }}
                        className="btn-secondary" style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12 }}>
                        Zachowaj
                      </button>
                      <button onClick={e => { e.stopPropagation(); deleteAll(group); }}
                        style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, background: 'rgba(236,72,153,0.15)', border: '1px solid rgba(236,72,153,0.3)', color: '#ec4899', cursor: 'pointer' }}>
                        Usuń
                      </button>
                      <button onClick={e => { e.stopPropagation(); mergeGroup(group); }}
                        style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)', color: '#8b5cf6', cursor: 'pointer' }}>
                        Scal
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right action panel */}
          {selectedGroup && (
            <div style={{
              width: 200, flexShrink: 0,
              background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
              borderRadius: 12, padding: 16,
              position: 'sticky', top: 0, alignSelf: 'flex-start',
            }}>
              <h4 style={{ color: '#e6f7ff', fontSize: 13, fontWeight: 600, margin: '0 0 14px' }}>Akcje grupowe</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <button onClick={() => keepFirst(selectedGroup)} className="btn-secondary"
                  style={{ padding: '12px', borderRadius: 8, fontSize: 13, width: '100%', display: 'block' }}>
                  Zachowaj
                </button>
                <button onClick={() => deleteAll(selectedGroup)}
                  style={{ padding: '12px', borderRadius: 8, fontSize: 13, width: '100%', display: 'block', background: 'rgba(236,72,153,0.15)', border: '1px solid rgba(236,72,153,0.4)', color: '#ec4899', cursor: 'pointer', fontWeight: 600 }}>
                  Usuń
                </button>
                <button onClick={() => mergeGroup(selectedGroup)}
                  style={{ padding: '12px', borderRadius: 8, fontSize: 13, width: '100%', display: 'block', background: 'linear-gradient(135deg, rgba(139,92,246,0.3), rgba(0,212,255,0.3))', border: '1px solid rgba(139,92,246,0.4)', color: '#e6f7ff', cursor: 'pointer', fontWeight: 600 }}>
                  Scal tagi
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DuplicatesView;
