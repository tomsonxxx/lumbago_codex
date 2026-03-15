
import React from 'react';
import { Playlist } from '../types';

interface AddToPlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  playlists: Playlist[];
  onSelect: (playlistId: string) => void;
  onCreateNew: (name: string) => void;
}

const AddToPlaylistModal: React.FC<AddToPlaylistModalProps> = ({ 
  isOpen, onClose, playlists, onSelect, onCreateNew 
}) => {
  const [newName, setNewName] = React.useState('');
  const [mode, setMode] = React.useState<'select' | 'create'>('select');

  if (!isOpen) return null;

  const handleCreate = (e: React.FormEvent) => {
      e.preventDefault();
      if(newName.trim()) {
          onCreateNew(newName.trim());
          setNewName('');
      }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex justify-center items-center z-[70]" onClick={onClose}>
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-sm animate-fade-in-scale" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Dodaj do playlisty</h3>
        
        {mode === 'select' ? (
            <>
                <div className="max-h-60 overflow-y-auto space-y-2 mb-4">
                    {playlists.length === 0 ? (
                        <p className="text-sm text-slate-500 text-center py-4">Brak playlist.</p>
                    ) : (
                        playlists.map(pl => (
                            <button
                                key={pl.id}
                                onClick={() => onSelect(pl.id)}
                                className="w-full text-left px-4 py-3 bg-slate-100 dark:bg-slate-700 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 rounded-md transition-colors text-slate-800 dark:text-slate-200"
                            >
                                {pl.name} <span className="text-xs text-slate-500 ml-1">({pl.trackIds.length})</span>
                            </button>
                        ))
                    )}
                </div>
                <button 
                    onClick={() => setMode('create')}
                    className="w-full py-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 border border-dashed border-indigo-300 dark:border-indigo-700 rounded-md hover:bg-indigo-50 dark:hover:bg-indigo-900/20"
                >
                    + Utwórz nową playlistę
                </button>
            </>
        ) : (
            <form onSubmit={handleCreate}>
                <input 
                    type="text" 
                    value={newName} 
                    onChange={e => setNewName(e.target.value)}
                    placeholder="Nazwa nowej playlisty"
                    className="w-full p-2 mb-4 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded focus:ring-2 focus:ring-indigo-500 outline-none dark:text-white"
                    autoFocus
                />
                <div className="flex gap-2">
                    <button type="button" onClick={() => setMode('select')} className="flex-1 py-2 text-sm bg-slate-200 dark:bg-slate-700 rounded hover:opacity-90 dark:text-white">Anuluj</button>
                    <button type="submit" className="flex-1 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-500">Utwórz i Dodaj</button>
                </div>
            </form>
        )}
        
        <button onClick={onClose} className="absolute top-2 right-2 text-slate-400 hover:text-slate-600">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
        </button>
      </div>
    </div>
  );
};

export default AddToPlaylistModal;
