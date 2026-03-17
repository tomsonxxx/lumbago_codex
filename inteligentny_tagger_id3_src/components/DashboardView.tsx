import React from 'react';
import { ActivityEntry, ViewType } from '../types';

interface DashboardViewProps {
  activityLog: ActivityEntry[];
  fileCount: number;
  onNavigate: (view: ViewType) => void;
}

const formatRelativeTime = (ts: number): string => {
  const diff = Date.now() - ts;
  if (diff < 60000) return 'Przed chwilą';
  if (diff < 3600000) return `${Math.floor(diff / 60000)} min temu`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} godz. temu`;
  return `${Math.floor(diff / 86400000)} dni temu`;
};

const activityIcons: Record<ActivityEntry['type'], React.ReactNode> = {
  import: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" strokeWidth="2">
      <polyline points="8 17 12 21 16 17"/><line x1="12" y1="12" x2="12" y2="21"/>
      <path d="M20.88 18.09A5 5 0 0018 9h-1.26A8 8 0 103 16.29"/>
    </svg>
  ),
  ai_tag: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="2">
      <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
  duplicate_found: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ec4899" strokeWidth="2">
      <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
    </svg>
  ),
  tags_edited: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2">
      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
    </svg>
  ),
  export: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  ),
};

const card: React.CSSProperties = {
  background: 'rgba(13, 17, 42, 0.85)',
  border: '1px solid rgba(0, 212, 255, 0.15)',
  borderRadius: 16,
  padding: 24,
  backdropFilter: 'blur(12px)',
};

const DashboardView: React.FC<DashboardViewProps> = ({ activityLog, fileCount, onNavigate }) => {
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: '#e6f7ff', margin: 0 }}>
          Witaj w <span style={{ background: 'linear-gradient(135deg, #00d4ff, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Lumbago Music AI</span>
        </h1>
        <p style={{ color: '#94a3b8', marginTop: 6, fontSize: 14 }}>
          {fileCount > 0 ? `Biblioteka zawiera ${fileCount} plików audio` : 'Zacznij od zaimportowania plików muzycznych'}
        </p>
      </div>

      {/* Top 3 cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Stwórz Nowy Utwór */}
        <div style={{ ...card, borderColor: 'rgba(0,212,255,0.2)' }}>
          <h3 style={{ color: '#e6f7ff', fontSize: 15, fontWeight: 600, margin: '0 0 16px' }}>Stwórz Nowy Utwór</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <button
              onClick={() => onNavigate('tagger')}
              className="btn-cta"
              style={{ padding: '10px 16px', borderRadius: 8, fontSize: 13, fontWeight: 600, width: '100%' }}
            >
              Generuj Piosenkę
            </button>
            <button
              onClick={() => onNavigate('import')}
              className="btn-secondary"
              style={{ padding: '10px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500, width: '100%' }}
            >
              Komponuj Samodzielnie
            </button>
          </div>
        </div>

        {/* Gotowe Szablony */}
        <div style={{ ...card, borderColor: 'rgba(139,92,246,0.2)' }}>
          <h3 style={{ color: '#e6f7ff', fontSize: 15, fontWeight: 600, margin: '0 0 16px' }}>Gotowe Szablony</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <button
              onClick={() => onNavigate('library')}
              className="btn-secondary"
              style={{ padding: '10px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500, width: '100%', borderColor: 'rgba(139,92,246,0.4)', color: '#a78bfa' }}
            >
              Przeglądaj Szablony
            </button>
            <button
              onClick={() => onNavigate('library')}
              className="btn-secondary"
              style={{ padding: '10px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500, width: '100%', borderColor: 'rgba(139,92,246,0.4)', color: '#a78bfa' }}
            >
              Popularne Style
            </button>
          </div>
        </div>

        {/* Szybkie Akcje */}
        <div style={{ ...card, borderColor: 'rgba(236,72,153,0.2)' }}>
          <h3 style={{ color: '#e6f7ff', fontSize: 15, fontWeight: 600, margin: '0 0 12px' }}>Szybkie Akcje</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {[
              { icon: '📁', label: 'Importuj Pliki', view: 'import' as ViewType },
              { icon: '🔍', label: 'Znajdź Duplikaty', view: 'duplicates' as ViewType },
              { icon: '🏷️', label: 'Edytuj Tagi', view: 'library' as ViewType },
            ].map(action => (
              <button
                key={action.view}
                onClick={() => onNavigate(action.view)}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '10px 14px', borderRadius: 8,
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  cursor: 'pointer', width: '100%',
                  color: '#e6f7ff', fontSize: 13, transition: 'all 0.15s',
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(0,212,255,0.08)'; (e.currentTarget as HTMLElement).style.borderColor = 'rgba(0,212,255,0.2)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.03)'; (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.06)'; }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span>{action.icon}</span>
                  <span>{action.label}</span>
                </span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Ostatnia Aktywność */}
      <div style={card}>
        <h3 style={{ color: '#e6f7ff', fontSize: 15, fontWeight: 600, margin: '0 0 16px' }}>Ostatnia Aktywność</h3>
        {activityLog.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#94a3b8', padding: '20px 0', fontSize: 13 }}>
            Brak aktywności. Zaimportuj pliki, aby rozpocząć.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {activityLog.slice(0, 8).map(entry => (
              <div
                key={entry.id}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '10px 12px', borderRadius: 8,
                  background: 'rgba(255,255,255,0.02)',
                  transition: 'background 0.15s',
                }}
              >
                <span style={{ flexShrink: 0 }}>{activityIcons[entry.type]}</span>
                <span style={{ flex: 1, fontSize: 13, color: '#cbd5e1' }}>{entry.message}</span>
                <span style={{ fontSize: 11, color: '#64748b', flexShrink: 0 }}>{formatRelativeTime(entry.timestamp)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats row */}
      {fileCount > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginTop: 20 }}>
          {[
            { label: 'Pliki audio', value: fileCount, color: '#00d4ff' },
            { label: 'Ostatnio dodane', value: activityLog.filter(a => a.type === 'import').length, color: '#8b5cf6' },
            { label: 'Otagowane AI', value: activityLog.filter(a => a.type === 'ai_tag').length, color: '#ec4899' },
            { label: 'Wyeksportowane', value: activityLog.filter(a => a.type === 'export').length, color: '#4ade80' },
          ].map(stat => (
            <div key={stat.label} style={{ ...card, padding: 16, textAlign: 'center' }}>
              <div style={{ fontSize: 28, fontWeight: 700, color: stat.color }}>{stat.value}</div>
              <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>{stat.label}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DashboardView;
