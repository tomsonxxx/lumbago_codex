import React, { useState } from 'react';
import { ViewType } from '../types';

interface NavItem {
  id: ViewType;
  label: string;
  icon: React.ReactNode;
}

const HomeIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);

const LibraryIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
  </svg>
);

const ImportIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="8 17 12 21 16 17"/><line x1="12" y1="12" x2="12" y2="21"/>
    <path d="M20.88 18.09A5 5 0 0018 9h-1.26A8 8 0 103 16.29"/>
  </svg>
);

const DuplicatesIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
  </svg>
);

const PlayerIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/>
  </svg>
);

const TaggerIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2a10 10 0 100 20A10 10 0 0012 2z"/>
    <path d="M12 8v4l3 3"/>
    <circle cx="12" cy="12" r="1" fill="currentColor"/>
  </svg>
);

const ConverterIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/>
    <polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/>
  </svg>
);

const SettingsIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
  </svg>
);

interface SidebarProps {
  activeView: ViewType;
  onNavigate: (view: ViewType) => void;
  fileCount: number;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Strona główna', icon: <HomeIcon /> },
  { id: 'library', label: 'Biblioteka', icon: <LibraryIcon /> },
  { id: 'import', label: 'Import', icon: <ImportIcon /> },
  { id: 'duplicates', label: 'Duplikaty', icon: <DuplicatesIcon /> },
  { id: 'player', label: 'Odtwarzacz', icon: <PlayerIcon /> },
  { id: 'tagger', label: 'Smart Tagger AI', icon: <TaggerIcon /> },
  { id: 'converter', label: 'Konwerter XML', icon: <ConverterIcon /> },
];

const Sidebar: React.FC<SidebarProps> = ({ activeView, onNavigate, fileCount }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      style={{
        width: expanded ? 220 : 64,
        minWidth: expanded ? 220 : 64,
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(8,10,28,0.98)',
        borderRight: '1px solid rgba(0,212,255,0.1)',
        transition: 'width 0.25s ease',
        overflow: 'hidden',
        zIndex: 20,
        position: 'relative',
      }}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      {/* Logo */}
      <div style={{
        height: 64,
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        borderBottom: '1px solid rgba(0,212,255,0.08)',
        flexShrink: 0,
        gap: 12,
      }}>
        <div style={{
          width: 32, height: 32,
          borderRadius: 8,
          background: 'linear-gradient(135deg, #00d4ff, #8b5cf6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
          fontSize: 13, fontWeight: 700, color: 'white',
        }}>LM</div>
        {expanded && (
          <span style={{ color: '#e6f7ff', fontWeight: 600, fontSize: 14, whiteSpace: 'nowrap', overflow: 'hidden' }}>
            Music AI
          </span>
        )}
      </div>

      {/* File count badge */}
      {fileCount > 0 && expanded && (
        <div style={{ padding: '8px 16px' }}>
          <div style={{
            background: 'rgba(0,212,255,0.08)',
            border: '1px solid rgba(0,212,255,0.2)',
            borderRadius: 8,
            padding: '6px 10px',
            fontSize: 11,
            color: '#00d4ff',
            textAlign: 'center',
          }}>
            {fileCount} plików w bibliotece
          </div>
        </div>
      )}

      {/* Nav items */}
      <nav style={{ flex: 1, padding: '8px 0', overflowY: 'auto', overflowX: 'hidden' }}>
        {navItems.map(item => {
          const isActive = activeView === item.id;
          return (
            <div
              key={item.id}
              className="sidebar-nav-item"
              onClick={() => onNavigate(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '10px 16px',
                gap: 12,
                cursor: 'pointer',
                borderLeft: isActive ? '2px solid #00d4ff' : '2px solid transparent',
                background: isActive ? 'rgba(0,212,255,0.1)' : 'transparent',
                color: isActive ? '#00d4ff' : '#94a3b8',
                transition: 'all 0.15s',
                position: 'relative',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={e => {
                if (!isActive) (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)';
              }}
              onMouseLeave={e => {
                if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent';
              }}
            >
              <span style={{ flexShrink: 0 }}>{item.icon}</span>
              {expanded && (
                <span style={{ fontSize: 13, fontWeight: isActive ? 600 : 400, overflow: 'hidden' }}>
                  {item.label}
                </span>
              )}
              {!expanded && (
                <span className="sidebar-tooltip">{item.label}</span>
              )}
            </div>
          );
        })}
      </nav>

      {/* Settings at bottom */}
      <div style={{ borderTop: '1px solid rgba(0,212,255,0.08)', flexShrink: 0 }}>
        <div
          className="sidebar-nav-item"
          onClick={() => onNavigate('settings')}
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '10px 16px',
            gap: 12,
            cursor: 'pointer',
            borderLeft: activeView === 'settings' ? '2px solid #00d4ff' : '2px solid transparent',
            background: activeView === 'settings' ? 'rgba(0,212,255,0.1)' : 'transparent',
            color: activeView === 'settings' ? '#00d4ff' : '#94a3b8',
            transition: 'all 0.15s',
            position: 'relative',
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={e => {
            if (activeView !== 'settings') (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)';
          }}
          onMouseLeave={e => {
            if (activeView !== 'settings') (e.currentTarget as HTMLElement).style.background = 'transparent';
          }}
        >
          <span style={{ flexShrink: 0 }}><SettingsIcon /></span>
          {expanded && <span style={{ fontSize: 13 }}>Ustawienia</span>}
          {!expanded && <span className="sidebar-tooltip">Ustawienia</span>}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
