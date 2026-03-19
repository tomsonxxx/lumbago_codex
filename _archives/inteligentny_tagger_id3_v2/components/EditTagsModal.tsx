import React, { useState, useEffect, useMemo } from 'react';
import { AudioFile, ID3Tags } from '../types';
import AlbumCover from './AlbumCover';

interface EditTagsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (tags: ID3Tags) => void;
  onApply: (tags: ID3Tags) => void;
  file: AudioFile;
  onManualSearch: (query: string, file: AudioFile) => Promise<void>;
  onZoomCover: (imageUrl: string) => void;
  isApplying: boolean;
  isDirectAccessMode: boolean;
}

const EditTagsModal: React.FC<EditTagsModalProps> = ({
  isOpen,
  onClose,
  onSave,
  onApply,
  file,
  onManualSearch,
  onZoomCover,
  isApplying,
  isDirectAccessMode,
}) => {
  const [tags, setTags] = useState<ID3Tags>({});
  const [manualQuery, setManualQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && file) {
      setTags(file.fetchedTags || file.originalTags || {});
      setManualQuery(file.file.name);
      setSearchError(null);
    }
  }, [isOpen, file]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setTags((prevTags) => ({
      ...prevTags,
      [name]: type === 'number' ? (value ? Number(value) : undefined) : value,
    }));
  };

  const handleSave = () => {
    onSave(tags);
  };

  const handleSearch = async () => {
    setIsSearching(true);
    setSearchError(null);
    try {
      await onManualSearch(manualQuery, file);
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "Wystąpił nieznany błąd wyszukiwania.");
    } finally {
      setIsSearching(false);
    }
  };
  
  useEffect(() => {
      if (file) {
          setTags(file.fetchedTags || file.originalTags || {});
      }
  }, [file?.fetchedTags]);
  
  const initialTags = useMemo(() => file.fetchedTags || file.originalTags || {}, [file.fetchedTags, file.originalTags]);
  const hasChanges = useMemo(() => JSON.stringify(tags) !== JSON.stringify(initialTags), [tags, initialTags]);

  if (!isOpen) return null;

  const tagFields: (keyof Omit<ID3Tags, 'albumCoverUrl' | 'comments'>)[] = [
    'title', 'artist', 'albumArtist', 'album', 'year', 'trackNumber', 'discNumber', 'genre', 'composer', 'originalArtist', 'mood', 'copyright', 'encodedBy', 'bpm', 'key', 'bitrate', 'sampleRate'
  ];
  const tagLabels: Record<string, string> = {
    title: 'Tytuł', artist: 'Wykonawca', albumArtist: 'Wykonawca albumu', album: 'Album',
    year: 'Rok', genre: 'Gatunek', mood: 'Nastrój', comments: 'Komentarze',
    bitrate: 'Bitrate (kbps)', sampleRate: 'Sample Rate (Hz)', trackNumber: 'Numer utworu',
    discNumber: 'Numer dysku', composer: 'Kompozytor', copyright: 'Prawa autorskie',
    encodedBy: 'Zakodowane przez', originalArtist: 'Oryginalny wykonawca',
    bpm: 'BPM', key: 'Tonacja (Camelot)'
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-white mb-2">Edytuj Tagi</h2>
        <p className="text-sm text-slate-400 mb-4 truncate" title={file.file.name}>
          {file.webkitRelativePath || file.file.name}
        </p>

        <div className="mb-6 p-4 bg-slate-900/50 rounded-lg">
           {/* ... (Manual Search Section - no changes) ... */}
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          <div className="md:w-1/4 flex flex-col items-center">
            {/* ... (Album Cover Section - no changes) ... */}
          </div>
          <div className="md:w-3/4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {tagFields.map((key) => (
                <div key={key} className={['title', 'album', 'copyright'].includes(key) ? 'sm:col-span-2' : ''}>
                  <label htmlFor={key} className="block text-sm font-medium text-slate-300">
                    {tagLabels[key]}
                  </label>
                  <input
                    type={['bitrate', 'sampleRate', 'bpm'].includes(key) ? 'number' : 'text'}
                    name={key} id={key} value={tags[key] as any || ''} onChange={handleChange}
                    className="mt-1 block w-full bg-slate-900 border border-slate-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-indigo-500 sm:text-sm"
                    placeholder={`Wprowadź ${tagLabels[key]?.toLowerCase()}`}
                  />
                </div>
              ))}
            </div>
            <div className="mt-4">
                {/* ... (Comments Textarea - no changes) ... */}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700 rounded-md hover:bg-slate-600">Anuluj</button>
          <button onClick={handleSave} className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500" title="Zapisuje zmiany w pamięci podręcznej aplikacji do późniejszego pobrania lub zapisu.">
            Zapisz
          </button>
          {isDirectAccessMode && (
            <button 
              onClick={() => onApply(tags)} 
              disabled={isApplying || !hasChanges}
              className="px-4 py-2 text-sm font-bold text-white bg-green-600 rounded-md hover:bg-green-500 disabled:bg-green-400 disabled:cursor-not-allowed flex items-center justify-center w-[160px]"
              title="Zapisuje zmiany i natychmiast nadpisuje oryginalny plik. Dostępne tylko w trybie bezpośredniego dostępu."
            >
              {isApplying ? (
                  <><span className="btn-spinner !mr-2"></span><span>Zapisuję...</span></>
              ) : (
                  'Zastosuj zmiany'
              )}
            </button>
          )}
        </div>
        <style>{`.animate-fade-in-scale { animation: fade-in-scale 0.2s ease-out forwards; } @keyframes fade-in-scale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }`}</style>
      </div>
    </div>
  );
};

export default EditTagsModal;
