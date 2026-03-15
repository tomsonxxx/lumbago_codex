
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
      // After a successful search, the new tags will flow down via props,
      // and the useEffect will update the local state.
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : "Wystąpił nieznany błąd wyszukiwania.");
    } finally {
      setIsSearching(false);
    }
  };
  
  // This effect will trigger when the parent component updates the file with new tags after a search
  useEffect(() => {
      if (file) {
          setTags(file.fetchedTags || file.originalTags || {});
      }
  }, [file?.fetchedTags]);
  
  const initialTags = useMemo(() => file.fetchedTags || file.originalTags || {}, [file.fetchedTags, file.originalTags]);
  const hasChanges = useMemo(() => JSON.stringify(tags) !== JSON.stringify(initialTags), [tags, initialTags]);

  if (!isOpen) return null;

  const tagFields: (keyof Omit<ID3Tags, 'albumCoverUrl' | 'comments'>)[] = [
    'title', 'artist', 'albumArtist', 'album', 'year', 'trackNumber', 'discNumber', 'genre', 'composer', 'originalArtist', 'mood', 'copyright', 'encodedBy', 'bitrate', 'sampleRate'
  ];
  const tagLabels: Record<string, string> = {
    title: 'Tytuł',
    artist: 'Wykonawca',
    albumArtist: 'Wykonawca albumu',
    album: 'Album',
    year: 'Rok',
    genre: 'Gatunek',
    mood: 'Nastrój',
    comments: 'Komentarze',
    bitrate: 'Bitrate (kbps)',
    sampleRate: 'Sample Rate (Hz)',
    trackNumber: 'Numer utworu',
    discNumber: 'Numer dysku',
    composer: 'Kompozytor',
    copyright: 'Prawa autorskie',
    encodedBy: 'Zakodowane przez',
    originalArtist: 'Oryginalny wykonawca',
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Edytuj Tagi</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 truncate" title={file.file.name}>
          Oryginalna nazwa: {file.file.name}
        </p>

        {/* Manual Search Section */}
        <div className="mb-6 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
           <label htmlFor="manualQuery" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
             Ręczne wyszukiwanie tagów
           </label>
           <div className="flex space-x-2">
             <input
               type="text"
               id="manualQuery"
               value={manualQuery}
               onChange={(e) => setManualQuery(e.target.value)}
               className="flex-grow bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm py-2 px-3 text-slate-900 dark:text-white focus:outline-none focus:ring-indigo-500 sm:text-sm"
               placeholder="Np. Artist - Song Title"
             />
             <button onClick={handleSearch} disabled={isSearching || !manualQuery} className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed flex items-center">
               {isSearching ? (
                 <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                   <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                   <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                 </svg>
               ) : 'Szukaj'}
             </button>
           </div>
           {searchError && <p className="text-xs text-red-500 mt-2">{searchError}</p>}
        </div>

        {/* Tags Form */}
        <div className="flex flex-col md:flex-row gap-6">
          <div className="md:w-1/4 flex flex-col items-center">
            <div className="relative group cursor-pointer" onClick={() => tags.albumCoverUrl && onZoomCover(tags.albumCoverUrl)}>
                <AlbumCover tags={tags} className="w-48 h-48" />
                {tags.albumCoverUrl && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-md">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" /></svg>
                    </div>
                )}
            </div>
             <label htmlFor="albumCoverUrl" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mt-4 self-stretch">
               URL Okładki
             </label>
             <input
               type="text"
               name="albumCoverUrl"
               id="albumCoverUrl"
               value={tags.albumCoverUrl || ''}
               onChange={handleChange}
               className="mt-1 block w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm py-2 px-3 text-slate-900 dark:text-white focus:outline-none focus:ring-indigo-500 sm:text-sm"
               placeholder="URL do obrazka"
             />
          </div>
          <div className="md:w-3/4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {tagFields.map((key) => (
                <div key={key} className={['title', 'album', 'copyright'].includes(key) ? 'sm:col-span-2' : ''}>
                  <label htmlFor={key} className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                    {tagLabels[key]}
                  </label>
                  <input
                    type={key === 'bitrate' || key === 'sampleRate' ? 'number' : 'text'}
                    name={key}
                    id={key}
                    value={tags[key] || ''}
                    onChange={handleChange}
                    className="mt-1 block w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm py-2 px-3 text-slate-900 dark:text-white focus:outline-none focus:ring-indigo-500 sm:text-sm"
                    placeholder={`Wprowadź ${tagLabels[key]?.toLowerCase()}`}
                  />
                </div>
              ))}
            </div>
            <div className="mt-4">
               <label htmlFor="comments" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  {tagLabels['comments']}
                </label>
                <textarea
                  name="comments"
                  id="comments"
                  value={tags.comments || ''}
                  onChange={handleChange}
                  rows={3}
                  className="mt-1 block w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm py-2 px-3 text-slate-900 dark:text-white focus:outline-none focus:ring-indigo-500 sm:text-sm"
                  placeholder="Wprowadź komentarze lub ciekawostki..."
                />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600">Anuluj</button>
          <button 
            onClick={handleSave} 
            className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500"
            title="Zapisuje zmiany w pamięci podręcznej aplikacji do późniejszego pobrania lub zapisu."
          >
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
