import React from 'react';
import { Library, Disc, Radio, Settings } from 'lucide-react';

export default function Sidebar() {
  return (
    <div style={{ width: '240px', background: 'var(--bg-secondary)', borderRight: '1px solid var(--bg-tertiary)', padding: '20px' }}>
      <h2 style={{ marginBottom: '30px', color: 'var(--accent-primary)' }}>Lumbago</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <NavItem icon={<Library size={18} />} label="Library" active />
        <NavItem icon={<Disc size={18} />} label="Playlists" />
        <NavItem icon={<Radio size={18} />} label="Scanner" />
        <NavItem icon={<Settings size={18} />} label="Settings" />
      </div>
    </div>
  );
}

const NavItem = ({ icon, label, active }) => (
  <div style={{ 
    display: 'flex', alignItems: 'center', gap: '12px', 
    padding: '10px 16px', borderRadius: '8px',
    background: active ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
    color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
    cursor: 'pointer'
  }}>
    {icon}
    <span>{label}</span>
  </div>
);