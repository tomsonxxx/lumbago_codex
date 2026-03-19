
import React from 'react';
import { Icons } from '../Icons';

export const Sidebar = ({ activeFeature, setActiveFeature }: { activeFeature: string, setActiveFeature: (f: string) => void }) => {
  const menuItems = [
    { id: 'libraryBrowser', label: 'Library Manager', icon: <Icons.ListMusic /> },
    { id: 'scanner', label: 'Import & Scanner', icon: <Icons.FolderInput /> },
    { id: 'library', label: 'Library Builder', icon: <Icons.Library /> },
    { id: 'player', label: 'Player & Waveform', icon: <Icons.Play /> },
    { id: 'duplicates', label: 'Duplicate Finder', icon: <Icons.Copy /> },
    { id: 'renamer', label: 'Renamer', icon: <Icons.FileDigit /> },
    { id: 'tagger', label: 'Smart Tagger AI', icon: <Icons.Sparkles /> },
    { id: 'recognizer', label: 'Audio Recognizer', icon: <Icons.Mic /> },
    { id: 'converter', label: 'XML Converter', icon: <Icons.RefreshCw /> },
    { id: 'playlist', label: 'Playlist Intel', icon: <Icons.ListMusic /> },
    { id: 'cratedigger', label: 'Crate Digger', icon: <Icons.Search /> },
    { id: 'recorder', label: 'Set Recorder', icon: <Icons.Disc /> },
    { id: 'cloud', label: 'Cloud Sync', icon: <Icons.Cloud /> },
    { id: 'metadata', label: 'Metadata Auto', icon: <Icons.Tags /> },
    { id: 'waveform', label: 'Color Waveform', icon: <Icons.Palette /> },
    { id: 'collections', label: 'Smart Collections', icon: <Icons.Library /> },
    { id: 'export', label: 'Export Manager', icon: <Icons.Share /> },
  ];

  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 h-screen overflow-y-auto fixed left-0 top-0">
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Lumbago Music AI
        </h1>
        <p className="text-xs text-gray-500 mt-1">v1.0.0 (Web Sim)</p>
      </div>
      <nav className="p-4 space-y-1">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveFeature(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-all ${
              activeFeature === item.id 
                ? 'bg-blue-600/20 text-blue-400 border border-blue-600/50' 
                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
            }`}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
};
