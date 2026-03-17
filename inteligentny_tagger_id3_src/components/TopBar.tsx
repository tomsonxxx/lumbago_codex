import React from 'react';
import { ViewType } from '../types';

const viewLabels: Record<ViewType, string> = {
  dashboard: 'Strona główna',
  library: 'Biblioteka',
  import: 'Import',
  duplicates: 'Duplikaty',
  settings: 'Ustawienia',
  player: 'Odtwarzacz',
  tagger: 'Smart Tagger AI',
  converter: 'Konwerter XML',
};

interface TopBarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  activeView: ViewType;
}

const TopBar: React.FC<TopBarProps> = ({ searchQuery, onSearchChange, activeView }) => {
  return (
    <div style={{
      height: 60,
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      gap: 16,
      background: 'rgba(8,10,28,0.8)',
      borderBottom: '1px solid rgba(0,212,255,0.08)',
      flexShrink: 0,
      backdropFilter: 'blur(12px)',
    }}>
      {/* Title */}
      <h2 style={{ color: '#e6f7ff', fontSize: 16, fontWeight: 600, margin: 0, flexShrink: 0 }}>
        {viewLabels[activeView]}
      </h2>

      {/* Search */}
      <div style={{ flex: 1, maxWidth: 480, position: 'relative' }}>
        <svg
          width="16" height="16"
          viewBox="0 0 24 24" fill="none" stroke="#94a3b8"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
        >
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          type="text"
          value={searchQuery}
          onChange={e => onSearchChange(e.target.value)}
          placeholder="Szukaj w bibliotece..."
          className="input-dark"
          style={{
            width: '100%',
            padding: '8px 12px 8px 36px',
            borderRadius: 8,
            fontSize: 13,
          }}
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            style={{
              position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8',
              padding: 2,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default TopBar;
