

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { AudioFile, ID3Tags } from '../types';
import { generatePath } from '../utils/filenameUtils';

interface RenameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (newPattern: string) => void;
  currentPattern: string;
  files: AudioFile[]; // Changed from exampleFile to a list
}

const placeholders: (keyof Omit<ID3Tags, 'albumCoverUrl' | 'comments' | 'mood' | 'bitrate' | 'sampleRate'>)[] = [
    'title', 
    'artist', 
    'albumArtist', 
    'album', 
    'trackNumber', 
    'discNumber', 
    'year', 
    'genre', 
    'composer', 
    'originalArtist', 
    'copyright', 
    'encodedBy'
];

const RenameModal: React.FC<RenameModalProps> = ({ isOpen, onClose, onSave, currentPattern, files }) => {
  const [pattern, setPattern] = useState(currentPattern);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setPattern(currentPattern);
    }
  }, [isOpen, currentPattern]);

  // Save pattern to localStorage in real-time as the user types
  useEffect(() => {
    if (isOpen) {
      localStorage.setItem('renamePattern', pattern);
    }
  }, [pattern, isOpen]);

  const handleSave = () => {
    // The onSave prop now triggers the confirmation modal in App.tsx
    onSave(pattern);
  };

  const insertPlaceholder = (placeholder: string) => {
    const text = `[${placeholder}]`;
    const input = inputRef.current;
    if (!input) return;

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const newPattern = pattern.substring(0, start) + text + pattern.substring(end);
    
    setPattern(newPattern);
    
    // Focus and set cursor position after placeholder
    setTimeout(() => {
      input.focus();
      input.setSelectionRange(start + text.length, start + text.length);
    }, 0);
  };
  
  const hasFilesForPreview = files && files.length > 0;
  
  const previews = useMemo(() => {
    if (!hasFilesForPreview) return [];
    return files.map(file => {
        const previewName = generatePath(pattern, file.fetchedTags || file.originalTags, file.file.name);
        return {
            id: file.id,
            originalName: file.webkitRelativePath || file.file.name, // Prefer relative path for preview
            newName: previewName,
            isTooLong: previewName.length > 255
        };
    });
  }, [pattern, files, hasFilesForPreview]);

  if (!isOpen) return null;

  const genericExampleTags: ID3Tags = {
      artist: 'Przykładowy Artysta',
      albumArtist: 'Artysta Albumu',
      title: 'Tytuł Utworu',
      album: 'Nazwa Albumu',
      year: '2024',
      genre: 'Pop',
      trackNumber: '01',
      discNumber: '1',
      composer: 'Kompozytor',
      copyright: '© 2024 Wytwórnia',
      encodedBy: 'Encoder',
      originalArtist: 'Oryginalny Wykonawca'
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-3xl mx-4 transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Ustaw szablon zmiany nazw</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Stwórz schemat, według którego będą generowane nowe nazwy plików. Użyj ukośnika <strong>/</strong> aby automatycznie tworzyć podfoldery, np. <code>[artist]/[album]/[title]</code>.
        </p>
        
        <div>
          <label htmlFor="pattern" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Szablon nazwy
          </label>
          <input
            ref={inputRef}
            type="text"
            id="pattern"
            value={pattern}
            onChange={(e) => setPattern(e.target.value)}
            className="mt-1 block w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm py-2 px-3 text-slate-900 dark:text-white focus:outline-none focus:ring-indigo-500 sm:text-sm font-mono"
            placeholder="[artist] - [title]"
          />
        </div>

        <div className="mt-3">
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Wstaw znacznik:</p>
            <div className="flex flex-wrap gap-2">
                {placeholders.map(p => (
                    <button 
                        key={p} 
                        onClick={() => insertPlaceholder(p)}
                        className="px-2 py-1 text-xs font-mono bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-md hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
                    >
                        [{p}]
                    </button>
                ))}
            </div>
        </div>

        {hasFilesForPreview ? (
             <div className="mt-4 p-3 bg-slate-100 dark:bg-slate-900 rounded-md max-h-64 overflow-y-auto">
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300 sticky top-0 bg-slate-100 dark:bg-slate-900 pb-2">Podgląd ({files.length} {files.length === 1 ? 'plik' : files.length > 1 && files.length < 5 ? 'pliki' : 'plików'}):</p>
                <ul className="text-xs font-mono mt-1 space-y-2">
                    {previews.map(previewItem => {
                        return (
                            <li key={previewItem.id} className="grid grid-cols-[1fr,auto,1fr] gap-2 items-center">
                                <span className="truncate text-slate-500 dark:text-slate-400 text-right" title={previewItem.originalName}>{previewItem.originalName}</span>
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-slate-400 dark:text-slate-500" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                                </svg>
                                <span className={`flex items-center truncate ${previewItem.isTooLong ? 'text-amber-600 dark:text-amber-500' : 'text-indigo-600 dark:text-indigo-400'}`} title={previewItem.newName}>
                                    {previewItem.isTooLong && (
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                                            <title>Wygenerowana ścieżka jest bardzo długa (&gt;255 znaków) i może powodować problemy w niektórych systemach plików.</title>
                                            <path fillRule="evenodd" d="M8.257 3.099c.636-1.21 2.852-1.21 3.488 0l6.233 11.896c.64 1.223-.453 2.755-1.744 2.755H3.768c-1.291 0-2.384-1.532-1.744-2.755L8.257 3.099zM10 13a1 1 0 110-2 1 1 0 010 2zm-1-4a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
                                        </svg>
                                    )}
                                    <span className="truncate">{previewItem.newName}</span>
                                </span>
                            </li>
                        )
                    })}
                </ul>
            </div>
        ) : (
            <div className="mt-4 p-3 bg-slate-100 dark:bg-slate-900 rounded-md">
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Podgląd:</p>
                <p className="text-sm text-indigo-600 dark:text-indigo-400 font-mono break-all mt-1" title={generatePath(pattern, genericExampleTags, 'przyklad.mp3')}>
                    {generatePath(pattern, genericExampleTags, 'przyklad.mp3')}
                </p>
            </div>
        )}


        <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600">Anuluj</button>
          <button onClick={handleSave} className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500">Zastosuj</button>
        </div>
      </div>
       <style>{`.animate-fade-in-scale { animation: fade-in-scale 0.2s ease-out forwards; } @keyframes fade-in-scale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }`}</style>
    </div>
  );
};

export default RenameModal;