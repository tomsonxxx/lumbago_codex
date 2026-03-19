
import React, { useState } from 'react';
import { Playlist } from '../types';

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
  playlists: Playlist[];
  onCreatePlaylist: (name: string) => void;
  onDeletePlaylist: (id: string) => void;
  favoritesCount: number;
}

const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onViewChange,
  playlists,
  onCreatePlaylist,
  onDeletePlaylist,
  favoritesCount
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newPlaylistName, setNewPlaylistName] = useState('');

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPlaylistName.trim()) {
      onCreatePlaylist(newPlaylistName.trim());
      setNewPlaylistName('');
      setIsCreating(false);
    }
  };

  const NavItem = ({ id, label, icon, count }: { id: string, label: string, icon: React.ReactNode, count?: number }) => {
    const isActive = activeView === id;
    return (
      <button
        onClick={() => onViewChange(id)}
        className={`w-full flex items-center justify-between px-3 py-2.5 mb-1 rounded-lg text-sm transition-all duration-200 group ${
          isActive
            ? 'bg-white/10 text-white font-medium shadow-[0_0_15px_rgba(142,240,255,0.1)]'
            : 'text-slate-400 hover:bg-white/5 hover:text-white'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className={`${isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'}`}>
             {icon}
          </div>
          <span>{label}</span>
        </div>
        {count !== undefined && count > 0 && (
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${isActive ? 'bg-cyan-500/20 text-cyan-400' : 'bg-slate-800 text-slate-500'}`}>
            {count}
          </span>
        )}
      </button>
    );
  };

  return (
    <aside className="w-64 bg-[#0a0a0f] border-r border-white/5 flex flex-col h-full flex-shrink-0">
      {/* Sekcja Główna */}
      <div className="p-4">
        <h3 className="text-xs font-bold text-slate-600 uppercase tracking-widest mb-3 pl-2">Menu</h3>
        <nav className="flex flex-col gap-1">
          <NavItem 
            id="home" 
            label="Start" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>}
          />
          <NavItem 
            id="library" 
            label="Biblioteka" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>}
          />
          <NavItem 
            id="favorites" 
            label="Ulubione" 
            count={favoritesCount}
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>}
          />
          <NavItem 
            id="scan" 
            label="Import" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>}
          />
        </nav>
      </div>

      {/* Sekcja Playlisty */}
      <div className="flex-1 overflow-y-auto px-4 custom-scrollbar mt-2">
        <div className="flex items-center justify-between mb-2 pl-2 pr-1">
            <h3 className="text-xs font-bold text-slate-600 uppercase tracking-widest">Playlisty</h3>
            <button 
                onClick={() => setIsCreating(true)} 
                className="text-slate-500 hover:text-cyan-400 transition-colors p-1"
                title="Nowa playlista"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            </button>
        </div>

        <div className="flex flex-col gap-0.5">
            {isCreating && (
                <form onSubmit={handleCreateSubmit} className="mb-2">
                    <input
                        type="text"
                        autoFocus
                        placeholder="Nazwa..."
                        value={newPlaylistName}
                        onChange={(e) => setNewPlaylistName(e.target.value)}
                        onBlur={() => !newPlaylistName && setIsCreating(false)}
                        className="w-full px-3 py-2 text-sm bg-slate-900 border border-slate-700 rounded-lg text-white focus:border-cyan-500 outline-none placeholder:text-slate-600"
                    />
                </form>
            )}

            {playlists.map(playlist => {
                const isActive = activeView === `playlist:${playlist.id}`;
                return (
                    <div key={playlist.id} className="group relative">
                        <button
                            onClick={() => onViewChange(`playlist:${playlist.id}`)}
                            className={`w-full flex items-center px-3 py-2 rounded-lg text-sm transition-all duration-200 ${
                                isActive
                                ? 'text-fuchsia-400 font-medium bg-fuchsia-500/10'
                                : 'text-slate-400 hover:text-white hover:bg-white/5'
                            }`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 mr-3 ${isActive ? 'text-fuchsia-400' : 'text-slate-600 group-hover:text-slate-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" /></svg>
                            <span className="truncate">{playlist.name}</span>
                        </button>
                        
                        <button 
                            onClick={(e) => { e.stopPropagation(); onDeletePlaylist(playlist.id); }}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                        </button>
                    </div>
                );
            })}
        </div>
      </div>

      {/* Narzędzia AI (Footer) */}
      <div className="p-4 mt-auto border-t border-white/5">
          <p className="text-[10px] text-slate-600 font-bold uppercase tracking-wider mb-2 pl-2">NARZĘDZIA AI</p>
          <div className="grid grid-cols-3 gap-2">
              <button onClick={() => onViewChange('tagger')} className="flex flex-col items-center justify-center p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-cyan-400 transition-colors" title="Smart Tagger">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z" /></svg>
              </button>
              <button onClick={() => onViewChange('duplicates')} className="flex flex-col items-center justify-center p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-[#39ff14] transition-colors" title="Duplikaty">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              </button>
              <button onClick={() => onViewChange('converter')} className="flex flex-col items-center justify-center p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-fuchsia-400 transition-colors" title="Konwerter">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              </button>
          </div>
      </div>
    </aside>
  );
};

export default Sidebar;
