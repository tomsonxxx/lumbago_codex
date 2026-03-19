import React from 'react';
import { AudioFile, Playlist } from '../types';

type Action = 
  | { type: 'analyze' }
  | { type: 'edit' }
  | { type: 'delete' }
  | { type: 'add-to-playlist', payload: string }
  | { type: 'remove-from-playlist' };


interface TrackContextMenuProps {
  menu: { x: number, y: number, file: AudioFile };
  onClose: () => void;
  onAction: (action: Action) => void;
  playlists: Playlist[];
  isPlaylistView: boolean;
}

const TrackContextMenu: React.FC<TrackContextMenuProps> = ({ menu, onClose, onAction, playlists, isPlaylistView }) => {
  const handleAction = (action: Action) => {
    onAction(action);
    onClose();
  };

  return (
    <div 
      className="context-menu"
      style={{ top: menu.y, left: menu.x }}
      onClick={(e) => e.stopPropagation()} // Prevent closing immediately
    >
        <button onClick={() => handleAction({ type: 'analyze' })} className="context-menu-item">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
            Analizuj z AI
        </button>
        <button onClick={() => handleAction({ type: 'edit' })} className="context-menu-item">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
            Edytuj tagi
        </button>

        <div className="context-menu-separator"></div>

        <div className="context-menu-submenu">
             <button className="context-menu-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path d="M5 3a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V5a2 2 0 00-2-2H5zm1 1h8a1 1 0 011 1v2a1 1 0 01-1 1H6a1 1 0 01-1-1V5a1 1 0 011-1zm8 8H6a1 1 0 00-1 1v2a1 1 0 001 1h8a1 1 0 001-1v-2a1 1 0 00-1-1z" /></svg>
                Dodaj do playlisty
                <svg xmlns="http://www.w3.org/2000/svg" className="ml-auto h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" /></svg>
            </button>
            <div className="context-menu-submenu-panel">
                {playlists.length > 0 ? playlists.map(p => (
                    <button key={p.id} onClick={() => handleAction({ type: 'add-to-playlist', payload: p.id })} className="context-menu-item w-full">
                        {p.name}
                    </button>
                )) : <span className="context-menu-item text-slate-500">Brak playlist</span>}
            </div>
        </div>

        {isPlaylistView && (
            <button onClick={() => handleAction({ type: 'remove-from-playlist' })} className="context-menu-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" /></svg>
                Usuń z playlisty
            </button>
        )}


        <div className="context-menu-separator"></div>

        <button onClick={() => handleAction({ type: 'delete' })} className="context-menu-item danger">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
            Usuń plik
        </button>
    </div>
  );
};

export default TrackContextMenu;