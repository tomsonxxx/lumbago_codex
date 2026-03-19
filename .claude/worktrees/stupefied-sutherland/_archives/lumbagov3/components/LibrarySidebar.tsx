
import React, { useState } from 'react';
import { Playlist } from '../types';

interface LibrarySidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
  playlists: Playlist[];
  onCreatePlaylist: (name: string) => void;
  onDeletePlaylist: (id: string) => void;
  onDownloadPlaylist?: (id: string) => void;
  totalTracks: number;
  favoritesCount: number;
}

const LibrarySidebar: React.FC<LibrarySidebarProps> = ({
  activeView,
  onViewChange,
  playlists,
  onCreatePlaylist,
  onDeletePlaylist,
  onDownloadPlaylist,
  totalTracks,
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
        className={`w-full flex items-center justify-between px-4 py-3 mb-1 text-sm transition-all duration-200 group ${
          isActive
            ? 'text-cyan-400 font-medium' // Neon color for text
            : 'text-slate-400 hover:text-white'
        }`}
      >
        <div className="flex items-center">
          <div className={`transition-all duration-300 ${isActive ? 'text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]' : 'text-slate-500 group-hover:text-slate-300'}`}>
             {icon}
          </div>
          <span className="ml-4">{label}</span>
        </div>
        {count !== undefined && (
          <span className={`text-[10px] font-bold ${isActive ? 'text-cyan-400' : 'text-slate-600'}`}>
            {count}
          </span>
        )}
      </button>
    );
  }

  return (
    <div className="w-64 flex-shrink-0 bg-[#050505] flex flex-col h-full overflow-hidden pt-4">
      {/* Sekcja BIBLIOTEKA */}
      <div className="px-6 py-4">
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 neon-text-blue">BIBLIOTEKA</h2>
      </div>
      
      <div className="px-2">
        <NavItem 
            id="library" 
            label="Wszystkie utwory" 
            count={totalTracks}
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
            label="Ostatnio dodane" // Changed label to match Image
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
      </div>

      {/* Sekcja PLAYLISTY */}
      <div className="px-6 pt-8 pb-2 flex justify-between items-end">
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest neon-text-blue">PLAYLISTY</h2>
      </div>

      <div className="flex-grow overflow-y-auto px-2 custom-scrollbar">
        {playlists.map(playlist => (
            <div key={playlist.id} className="group relative">
                <button
                    onClick={() => onViewChange(`playlist:${playlist.id}`)}
                    className={`w-full flex items-center px-4 py-2.5 text-sm transition-all duration-200 ${
                        activeView === `playlist:${playlist.id}`
                        ? 'text-cyan-400 font-medium'
                        : 'text-slate-400 hover:text-white'
                    }`}
                >
                    <div className={`mr-4 transition-colors ${activeView === `playlist:${playlist.id}` ? 'text-cyan-400 drop-shadow-[0_0_5px_cyan]' : 'text-slate-600 group-hover:text-slate-400'}`}>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>
                    </div>
                    <span className="truncate">{playlist.name}</span>
                </button>
                
                {/* Hover actions */}
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex opacity-0 group-hover:opacity-100 transition-opacity">
                    {onDownloadPlaylist && (
                        <button onClick={(e) => { e.stopPropagation(); onDownloadPlaylist(playlist.id); }} className="p-1.5 text-slate-500 hover:text-cyan-400">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                        </button>
                    )}
                    <button onClick={(e) => { e.stopPropagation(); onDeletePlaylist(playlist.id); }} className="p-1.5 text-slate-500 hover:text-red-500">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                    </button>
                </div>
            </div>
        ))}
        
        {isCreating ? (
            <form onSubmit={handleCreateSubmit} className="px-4 py-2">
                <input
                    type="text"
                    autoFocus
                    placeholder="Nazwa playlisty..."
                    value={newPlaylistName}
                    onChange={(e) => setNewPlaylistName(e.target.value)}
                    onBlur={() => !newPlaylistName && setIsCreating(false)}
                    className="w-full px-2 py-1 text-sm bg-slate-900 border border-slate-700 rounded text-white focus:border-cyan-500 outline-none"
                />
            </form>
        ) : (
            <button onClick={() => setIsCreating(true)} className="flex items-center px-4 py-3 text-sm text-slate-500 hover:text-cyan-400 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
                Nowa playlista
            </button>
        )}
      </div>
      
      {/* Narzędzia (Link to other tabs) */}
      <div className="p-4 border-t border-slate-900">
          <div className="flex gap-2">
              <button onClick={() => onViewChange('duplicates')} className="flex-1 py-2 rounded-lg bg-slate-900 text-xs text-slate-400 hover:text-white hover:bg-slate-800 transition-colors" title="Duplikaty">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mx-auto mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              </button>
              <button onClick={() => onViewChange('converter')} className="flex-1 py-2 rounded-lg bg-slate-900 text-xs text-slate-400 hover:text-white hover:bg-slate-800 transition-colors" title="Konwerter">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mx-auto mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
              </button>
          </div>
      </div>
    </div>
  );
};

export default LibrarySidebar;
