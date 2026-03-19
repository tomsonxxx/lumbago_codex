import React, { useState, useEffect } from 'react';
import { SmartCollection, Playlist } from '../types';

interface SidebarProps {
  activeView: { type: 'all' | 'collection' | 'playlist'; id: string | null };
  onActiveViewChange: (view: { type: 'all' | 'collection' | 'playlist'; id: string | null }) => void;
  smartCollections: SmartCollection[];
  onNewCollection: () => void;
  playlists: Playlist[];
  onNewPlaylist: () => void;
  onRenamePlaylist: (id: string, newName: string) => void;
  onDeletePlaylist: (id: string) => void;
  onAddTracksToPlaylist: (playlistId: string, trackIds: string[]) => void;
  onIntelliSortPlaylist: (playlistId: string) => void; // NOWY
  onExportPlaylist: (playlistId: string, format: 'rekordbox' | 'virtualdj') => void; // NOWY
}

const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onActiveViewChange,
  smartCollections,
  onNewCollection,
  playlists,
  onNewPlaylist,
  onRenamePlaylist,
  onDeletePlaylist,
  onAddTracksToPlaylist,
  onIntelliSortPlaylist,
  onExportPlaylist,
}) => {
  const [contextMenu, setContextMenu] = useState<{ x: number, y: number, playlistId: string } | null>(null);
  const [isEditing, setIsEditing] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [dragOverPlaylist, setDragOverPlaylist] = useState<string | null>(null);
  
  useEffect(() => {
    const closeMenu = () => setContextMenu(null);
    window.addEventListener('click', closeMenu);
    return () => window.removeEventListener('click', closeMenu);
  }, []);

  const handleContextMenu = (e: React.MouseEvent, playlistId: string) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, playlistId });
  };

  const startRename = () => {
    if (contextMenu) {
      const playlist = playlists.find(p => p.id === contextMenu.playlistId);
      if (playlist) {
        setIsEditing(contextMenu.playlistId);
        setEditingName(playlist.name);
      }
      setContextMenu(null);
    }
  };

  const finishRename = (e: React.FormEvent) => {
    e.preventDefault();
    if (isEditing && editingName.trim()) {
      onRenamePlaylist(isEditing, editingName.trim());
    }
    setIsEditing(null);
  };
  
  const handleDragOver = (e: React.DragEvent, playlistId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    setDragOverPlaylist(playlistId);
  };

  const handleDrop = (e: React.DragEvent, playlistId: string) => {
    e.preventDefault();
    setDragOverPlaylist(null);
    try {
        const data = JSON.parse(e.dataTransfer.getData('text/plain'));
        if ((data.source === 'trackList' || data.source === 'playlistReorder') && data.trackIds) {
          onAddTracksToPlaylist(playlistId, data.trackIds);
        }
    } catch (err) {
        console.error("Failed to parse D&D data:", err);
    }
  };

  const handleDragLeave = () => setDragOverPlaylist(null);

  return (
    <aside className="panel hidden lg:flex flex-col">
       <div className="mb-6">
        <h3 className="text-sm font-bold uppercase tracking-wider mb-2 pl-2 border-l-4" style={{ borderColor: 'var(--accent-cyan)' }}>📁 Sources</h3>
        <ul className="space-y-1">
          <li>
            <a href="#" onClick={(e) => { e.preventDefault(); onActiveViewChange({ type: 'all', id: null }); }}
               className={`flex items-center p-2 rounded-md text-sm font-medium transition-colors ${activeView.type === 'all' ? 'bg-accent-magenta/20 text-accent-magenta' : 'hover:bg-slate-700/50'}`}>
              <span className="mr-3">📚</span> All Tracks
            </a>
          </li>
          <li>
            <a href="#" onClick={(e) => { e.preventDefault(); alert('Funkcja w przygotowaniu!'); }}
               className={`flex items-center p-2 rounded-md text-sm font-medium transition-colors text-text-dim hover:bg-slate-700/50`}>
              <span className="mr-3">⭐</span> Favorites
            </a>
          </li>
          <li>
            <a href="#" onClick={(e) => { e.preventDefault(); alert('Funkcja w przygotowaniu!'); }}
               className={`flex items-center p-2 rounded-md text-sm font-medium transition-colors text-text-dim hover:bg-slate-700/50`}>
              <span className="mr-3">🕐</span> Recently Added
            </a>
          </li>
        </ul>
      </div>
       <div className="mb-6">
        <div className="flex justify-between items-center mb-2 pl-2 border-l-4" style={{ borderColor: 'var(--accent-cyan)'}}>
          <h3 className="text-sm font-bold uppercase tracking-wider">⚙️ Smart Collections</h3>
          <button onClick={onNewCollection} className="p-1 text-slate-400 hover:text-white" title="Nowa inteligentna kolekcja">+</button>
        </div>
        <ul className="space-y-1">
          {smartCollections.map(sc => (
            <li key={sc.id}>
              <a href="#" onClick={(e) => { e.preventDefault(); onActiveViewChange({ type: 'collection', id: sc.id }); }}
                 className={`flex items-center p-2 rounded-md text-sm font-medium transition-colors ${activeView.type === 'collection' && activeView.id === sc.id ? 'bg-accent-magenta/20 text-accent-magenta' : 'hover:bg-slate-700/50'}`}>
                {sc.name}
              </a>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex-grow flex flex-col min-h-0">
        <div className="flex justify-between items-center mb-2 pl-2 border-l-4" style={{ borderColor: 'var(--accent-magenta)'}}>
          <h3 className="text-sm font-bold uppercase tracking-wider">🎵 Playlists</h3>
          <button onClick={onNewPlaylist} className="p-1 text-slate-400 hover:text-white" title="Nowa playlista">+</button>
        </div>
        <ul className="space-y-1 overflow-y-auto pr-1">
          {playlists.map(p => (
            <li key={p.id} onDragOver={(e) => handleDragOver(e, p.id)} onDrop={(e) => handleDrop(e, p.id)} onDragLeave={handleDragLeave}>
              <a href="#" onClick={(e) => { e.preventDefault(); onActiveViewChange({ type: 'playlist', id: p.id }); }} onContextMenu={(e) => handleContextMenu(e, p.id)}
                 className={`flex items-center justify-between p-2 rounded-md text-sm font-medium transition-colors ${dragOverPlaylist === p.id ? 'bg-indigo-500/30' : ''} ${activeView.type === 'playlist' && activeView.id === p.id ? 'bg-accent-magenta/20 text-accent-magenta' : 'hover:bg-slate-700/50'}`}>
                {isEditing === p.id ? (
                    <form onSubmit={finishRename} className="w-full"><input type="text" value={editingName} onChange={(e) => setEditingName(e.target.value)} onBlur={(e) => finishRename(e)} autoFocus className="w-full bg-slate-900 text-white p-0 m-0 border-0 focus:ring-0"/></form>
                ) : ( <span className="truncate flex items-center">{p.name}</span> )}
                <span className="text-xs text-slate-400 ml-2">{p.trackIds.length}</span>
              </a>
            </li>
          ))}
        </ul>
      </div>

      {contextMenu && (
        <div 
          className="context-menu"
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <button onClick={startRename} className="context-menu-item">Zmień nazwę</button>
          <div className="context-menu-separator"></div>
          <button onClick={() => { onIntelliSortPlaylist(contextMenu.playlistId); setContextMenu(null); }} className="context-menu-item">Sortuj inteligentnie</button>
          <div className="context-menu-separator"></div>
          <button onClick={() => { onExportPlaylist(contextMenu.playlistId, 'rekordbox'); setContextMenu(null); }} className="context-menu-item">Eksportuj do Rekordbox (XML)</button>
          <button onClick={() => { onExportPlaylist(contextMenu.playlistId, 'virtualdj'); setContextMenu(null); }} className="context-menu-item">Eksportuj do VirtualDJ (XML)</button>
          <div className="context-menu-separator"></div>
          <button onClick={() => { onDeletePlaylist(contextMenu.playlistId); setContextMenu(null); }} className="context-menu-item danger">Usuń playlistę</button>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;