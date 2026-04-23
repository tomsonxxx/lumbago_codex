import React from 'react';
import Sidebar from './components/Sidebar';
import Library from './components/Library';
import Inspector from './components/Inspector';

export default function App() {
  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Library />
      </div>
      <Inspector />
    </div>
  );
}