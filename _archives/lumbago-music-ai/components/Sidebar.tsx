
import React from 'react';
import { Playlist } from '../types';

interface SidebarItemProps {
    icon: React.ReactNode; 
    label: string; 
    isActive?: boolean; 
    count?: number; 
    onClick?: () => void;
    onDelete?: (e: React.MouseEvent) => void;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ icon, label, isActive, count, onClick, onDelete }) => (
  <div 
    onClick={onClick}
    className={`
      flex items-center justify-between px-4 py-2.5 mx-2 rounded-lg cursor-pointer transition-all duration-300 group
      ${isActive 
        ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-neon' 
        : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 hover:shadow-neon-hover'
      }
    `}
  >
    <div className="flex items-center overflow-hidden">
      <span className={`flex-shrink-0 ${isActive ? 'text-indigo-100' : 'text-slate-500 group-hover:text-indigo-400 transition-colors'}`}>
        {icon}
      </span>
      <span className="ml-3 text-sm font-medium tracking-wide truncate">{label}</span>
    </div>
    <div className="flex items-center ml-2">
        {count !== undefined && (
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${isActive ? 'bg-indigo-500/50 text-white' : 'bg-slate-800 text-slate-500 group-hover:text-slate-300'}`}>
            {count}
        </span>
        )}
        {onDelete && (
            <button 
                onClick={(e) => { e.stopPropagation(); onDelete(e); }}
                className="ml-2 p-1 text-slate-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Usuń playlistę"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414-1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
            </button>
        )}
    </div>
  </div>
);

const SidebarSectionHeader: React.FC<{ children: React.ReactNode; action?: React.ReactNode }> = ({ children, action }) => (
    <div className="px-6 py-2 mt-4 flex items-center justify-between group">
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest opacity-80">{children}</span>
        {action}
    </div>
);

interface SidebarProps {
  totalFiles?: number;
  playlists: Playlist[];
  activePlaylistId: string | null;
  onPlaylistSelect: (id: string | null) => void;
  onCreatePlaylist: () => void;
  onDeletePlaylist: (id: string) => void;
  onShowRecentlyAdded: () => void;
  onShowDuplicates: () => void;
  onShowXmlConverter: () => void;
  onSmartPlaylist: () => void; 
}

const Sidebar: React.FC<SidebarProps> = ({ 
    totalFiles, 
    playlists, 
    activePlaylistId, 
    onPlaylistSelect, 
    onCreatePlaylist,
    onDeletePlaylist,
    onShowRecentlyAdded,
    onShowDuplicates,
    onShowXmlConverter,
    onSmartPlaylist
}) => {
  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-full flex-shrink-0 z-30 shadow-2xl">
      <div className="h-16 flex items-center px-6 border-b border-slate-800/50 bg-slate-950/50 backdrop-blur-sm">
        <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/20 mr-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
                <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
            </svg>
        </div>
        <div>
            <h1 className="text-white font-bold text-lg tracking-tight leading-none">Lumbago AI</h1>
            <span className="text-[10px] text-indigo-400 font-medium tracking-wider">MUSIC MANAGER</span>
        </div>
      </div>

      <div className="flex-grow overflow-y-auto py-2 space-y-1 scrollbar-thin scrollbar-thumb-slate-800">
        <div>
            <SidebarSectionHeader>Biblioteka</SidebarSectionHeader>
            <SidebarItem 
                isActive={activePlaylistId === null}
                onClick={() => onPlaylistSelect(null)}
                count={totalFiles || 0}
                label="Wszystkie utwory" 
                icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>} 
            />
            <SidebarItem 
                label="Ostatnio dodane" 
                onClick={onShowRecentlyAdded}
                icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>} 
            />
        </div>

        <div>
            <SidebarSectionHeader 
                action={
                    <div className="flex space-x-1">
                        <button onClick={onSmartPlaylist} className="text-indigo-400 hover:text-indigo-200 transition-colors" title="Generuj Smart Playlist (AI)">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8 6.5 10.866a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z" clipRule="evenodd" /></svg>
                        </button>
                        <button onClick={onCreatePlaylist} className="text-slate-500 hover:text-indigo-400 transition-colors" title="Nowa playlista">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" /></svg>
                        </button>
                    </div>
                }
            >
                Playlisty
            </SidebarSectionHeader>
            {playlists.length === 0 ? (
                <div className="px-6 py-2 text-xs text-slate-600 italic">Brak playlist</div>
            ) : (
                playlists.map(playlist => (
                    <SidebarItem key={playlist.id} label={playlist.name} count={playlist.trackIds.length} isActive={activePlaylistId === playlist.id} onClick={() => onPlaylistSelect(playlist.id)} onDelete={() => onDeletePlaylist(playlist.id)} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 6l12-3" /></svg>} />
                ))
            )}
        </div>

        <div>
            <SidebarSectionHeader>Narzędzia</SidebarSectionHeader>
            <SidebarItem label="Znajdź Duplikaty" onClick={onShowDuplicates} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>} />
            <SidebarItem label="Konwerter XML" onClick={onShowXmlConverter} icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>} />
        </div>
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-900/30">
        <div className="bg-gradient-to-r from-slate-800 to-slate-800/50 rounded-lg p-3 border border-slate-700/50">
             <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-bold text-slate-400">Status Systemu</div>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
             </div>
             <div className="flex items-center space-x-2">
                 <span className="text-xs text-slate-500">AI Worker:</span>
                 <span className="text-xs text-green-400 font-mono">ONLINE</span>
             </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
