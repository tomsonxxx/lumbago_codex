import React, { useState } from 'react';
import { AudioFile } from '../types';

declare const saveAs: any;

interface XmlConverterViewProps {
  files: AudioFile[];
}

type XmlFormat = 'virtualdj' | 'rekordbox' | 'traktor';

const formatInfo: Record<XmlFormat, { label: string; ext: string; color: string; desc: string }> = {
  virtualdj: { label: 'VirtualDJ', ext: 'xml', color: '#00d4ff', desc: 'Format VirtualDJ 8/2023 Database XML' },
  rekordbox: { label: 'Rekordbox', ext: 'xml', color: '#ec4899', desc: 'Format Pioneer Rekordbox 6.x XML' },
  traktor: { label: 'Traktor', ext: 'nml', color: '#fbbf24', desc: 'Format Native Instruments Traktor NML' },
};

const generateVirtualDjXml = (files: AudioFile[]): string => {
  const tracks = files.map(f => {
    const t = f.fetchedTags || f.originalTags;
    return `    <Song FilePath="${f.webkitRelativePath || f.file.name}" Artist="${t.artist || ''}" Title="${t.title || f.file.name}" Album="${t.album || ''}" Genre="${t.genre || ''}" Bpm="${t.bpm || ''}" Key="${t.key || ''}" Year="${t.year || ''}" />`;
  }).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<VirtualDJ_Database Version="8.4">\n${tracks}\n</VirtualDJ_Database>`;
};

const generateRekordboxXml = (files: AudioFile[]): string => {
  const tracks = files.map((f, i) => {
    const t = f.fetchedTags || f.originalTags;
    return `      <TRACK TrackID="${i + 1}" Name="${t.title || f.file.name}" Artist="${t.artist || ''}" Album="${t.album || ''}" Genre="${t.genre || ''}" Bpm="${t.bpm || ''}" Tonality="${t.key || ''}" Year="${t.year || ''}" Location="${f.webkitRelativePath || f.file.name}" />`;
  }).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<DJ_PLAYLISTS Version="1.0.0">\n  <PRODUCT Name="rekordbox" Version="6.0.0" />\n  <COLLECTION Entries="${files.length}">\n${tracks}\n  </COLLECTION>\n</DJ_PLAYLISTS>`;
};

const generateTraktorNml = (files: AudioFile[]): string => {
  const tracks = files.map(f => {
    const t = f.fetchedTags || f.originalTags;
    return `    <ENTRY ARTIST="${t.artist || ''}" TITLE="${t.title || f.file.name}">\n      <LOCATION DIR="${f.webkitRelativePath || ''}" FILE="${f.file.name}" />\n      <INFO GENRE="${t.genre || ''}" KEY="${t.key || ''}" />\n    </ENTRY>`;
  }).join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<NML VERSION="23">\n  <COLLECTION ENTRIES="${files.length}">\n${tracks}\n  </COLLECTION>\n</NML>`;
};

const XmlConverterView: React.FC<XmlConverterViewProps> = ({ files }) => {
  const [exportFormat, setExportFormat] = useState<XmlFormat>('virtualdj');
  const [preview, setPreview] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [importedXml, setImportedXml] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  const selectedFiles = files.filter(f => f.isSelected);
  const targetFiles = selectedFiles.length > 0 ? selectedFiles : files;

  const generateXml = () => {
    switch (exportFormat) {
      case 'virtualdj': return generateVirtualDjXml(targetFiles);
      case 'rekordbox': return generateRekordboxXml(targetFiles);
      case 'traktor': return generateTraktorNml(targetFiles);
    }
  };

  const handlePreview = () => {
    setPreview(generateXml());
    setShowPreview(true);
  };

  const handleExport = () => {
    const xml = generateXml();
    const ext = formatInfo[exportFormat].ext;
    const blob = new Blob([xml], { type: 'text/xml;charset=utf-8;' });
    if (typeof saveAs !== 'undefined') {
      saveAs(blob, `lumbago-export-${exportFormat}.${ext}`);
    } else {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `lumbago-export-${exportFormat}.${ext}`;
      a.click();
    }
  };

  const handleImportDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => setImportedXml((ev.target?.result as string) || '');
    reader.readAsText(file);
  };

  const syntaxHighlight = (xml: string) =>
    xml
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/(&lt;\/?[\w:]+)/g, '<span class="xml-tag">$1</span>')
      .replace(/(&gt;)/g, '<span class="xml-tag">$1</span>')
      .replace(/([\w:]+)=/g, '<span class="xml-attr">$1</span>=')
      .replace(/"([^"]*)"/g, '"<span class="xml-value">$1</span>"');

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Import XML */}
        <div style={{
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: 16, padding: 20,
        }}>
          <h3 style={{ color: '#e6f7ff', fontSize: 15, fontWeight: 600, margin: '0 0 16px' }}>Import XML</h3>
          <div
            onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleImportDrop}
            className={isDragging ? 'drag-active' : ''}
            style={{
              border: `2px dashed ${isDragging ? '#00d4ff' : 'rgba(0,212,255,0.2)'}`,
              borderRadius: 10, padding: 24, textAlign: 'center',
              background: isDragging ? 'rgba(0,212,255,0.05)' : 'rgba(255,255,255,0.02)',
              marginBottom: 14, transition: 'all 0.2s', cursor: 'pointer',
            }}
            onClick={() => document.getElementById('xml-import-input')?.click()}
          >
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" strokeWidth="1.3" style={{ opacity: 0.6, marginBottom: 8 }}>
              <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
              <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3"/>
            </svg>
            <p style={{ color: '#94a3b8', fontSize: 12, margin: 0 }}>Przeciągnij plik XML/NML</p>
          </div>
          <input id="xml-import-input" type="file" accept=".xml,.nml" style={{ display: 'none' }}
            onChange={e => {
              const f = e.target.files?.[0];
              if (!f) return;
              const reader = new FileReader();
              reader.onload = ev => setImportedXml((ev.target?.result as string) || '');
              reader.readAsText(f);
            }}
          />

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(formatInfo).map(([key, info]) => (
              <div key={key} style={{
                padding: '6px 12px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                background: `rgba(${key === 'virtualdj' ? '0,212,255' : key === 'rekordbox' ? '236,72,153' : '251,191,36'},0.1)`,
                border: `1px solid ${info.color}40`,
                color: info.color,
              }}>
                {info.label}
              </div>
            ))}
          </div>

          {importedXml && (
            <div style={{ marginTop: 12 }}>
              <div style={{ padding: '8px 10px', borderRadius: 6, background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.2)', fontSize: 11, color: '#4ade80' }}>
                ✓ Załadowano {importedXml.split('\n').length} linii XML
              </div>
            </div>
          )}
        </div>

        {/* Export XML */}
        <div style={{
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(139,92,246,0.2)',
          borderRadius: 16, padding: 20,
        }}>
          <h3 style={{ color: '#e6f7ff', fontSize: 15, fontWeight: 600, margin: '0 0 16px' }}>Export XML</h3>

          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 11, color: '#94a3b8', display: 'block', marginBottom: 8 }}>Format docelowy</label>
            <select
              value={exportFormat}
              onChange={e => setExportFormat(e.target.value as XmlFormat)}
              className="input-dark"
              style={{ width: '100%', padding: '9px 12px', borderRadius: 8, fontSize: 13 }}
            >
              {Object.entries(formatInfo).map(([key, info]) => (
                <option key={key} value={key}>{info.label} (.{info.ext})</option>
              ))}
            </select>
            <p style={{ fontSize: 11, color: '#64748b', marginTop: 6 }}>
              {formatInfo[exportFormat].desc}
            </p>
          </div>

          <div style={{ padding: '10px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', marginBottom: 16 }}>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>
              Pliki do eksportu: <strong style={{ color: '#00d4ff' }}>{targetFiles.length}</strong>
              {selectedFiles.length > 0 && ' (zaznaczone)'}
            </span>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={handlePreview} className="btn-secondary"
              style={{ flex: 1, padding: '10px', borderRadius: 8, fontSize: 13 }}>
              Podgląd XML
            </button>
            <button onClick={handleExport} disabled={targetFiles.length === 0} className="btn-cta"
              style={{ flex: 1, padding: '10px', borderRadius: 8, fontSize: 13, fontWeight: 600 }}>
              Konwertuj i Pobierz
            </button>
          </div>
        </div>
      </div>

      {/* XML Preview */}
      {showPreview && preview && (
        <div style={{
          background: 'rgba(13,17,42,0.85)', border: '1px solid rgba(0,212,255,0.15)',
          borderRadius: 16, padding: 20,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ color: '#e6f7ff', fontSize: 15, fontWeight: 600, margin: 0 }}>Podgląd XML</h3>
            <button onClick={() => setShowPreview(false)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: 18 }}>×</button>
          </div>
          <pre
            dangerouslySetInnerHTML={{ __html: syntaxHighlight(preview.slice(0, 3000)) }}
            style={{
              background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: 16,
              fontSize: 11, overflowX: 'auto', overflowY: 'auto', maxHeight: 300,
              color: '#94a3b8', margin: 0,
              border: '1px solid rgba(255,255,255,0.05)',
            }}
          />
          {preview.length > 3000 && (
            <p style={{ fontSize: 11, color: '#64748b', marginTop: 8, marginBottom: 0 }}>
              ... (skrócono podgląd, eksport zawiera {targetFiles.length} pełnych rekordów)
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default XmlConverterView;
