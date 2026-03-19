import React, { useState, useMemo, useEffect } from 'react';
import { AudioFile, ID3Tags } from '../types';

interface BatchEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (tagsToApply: Partial<ID3Tags>) => void;
  files: AudioFile[];
}

type EditableTags = Pick<ID3Tags, 'artist' | 'albumArtist' | 'album' | 'year' | 'genre' | 'mood' | 'comments' | 'composer' | 'copyright' | 'encodedBy' | 'originalArtist' | 'discNumber' | 'bitrate' | 'sampleRate'>;
const editableTagKeys: (keyof EditableTags)[] = ['artist', 'albumArtist', 'album', 'year', 'genre', 'composer', 'originalArtist', 'discNumber', 'mood', 'copyright', 'encodedBy', 'comments', 'bitrate', 'sampleRate'];

const BatchEditModal: React.FC<BatchEditModalProps> = ({ isOpen, onClose, onSave, files }) => {
  const [tags, setTags] = useState<Partial<EditableTags>>({});
  const [fieldsToUpdate, setFieldsToUpdate] = useState<Record<keyof EditableTags, boolean>>(() =>
    editableTagKeys.reduce((acc, key) => ({ ...acc, [key]: false }), {} as Record<keyof EditableTags, boolean>)
  );

  const commonTags = useMemo<Partial<EditableTags>>(() => {
    if (!files || files.length === 0) return {};
    const firstFileTags: Partial<ID3Tags> = files[0].fetchedTags || {};
    const result: Partial<EditableTags> = {};

    for (const key of editableTagKeys) {
        const firstValue = firstFileTags[key];
        if (files.every(f => (f.fetchedTags?.[key] ?? '') === (firstValue ?? ''))) {
            if (key === 'bitrate' || key === 'sampleRate') {
                if (typeof firstValue === 'number' || typeof firstValue === 'undefined') {
                  result[key] = firstValue;
                }
            } else {
                if (typeof firstValue === 'string' || typeof firstValue === 'undefined') {
                  result[key] = firstValue;
                }
            }
        }
    }
    return result;
  }, [files]);

  useEffect(() => {
    if(isOpen) {
        setTags(commonTags);
        // Reset checkboxes on open
        setFieldsToUpdate(
          editableTagKeys.reduce((acc, key) => ({ ...acc, [key]: false }), {} as Record<keyof EditableTags, boolean>)
        );
    }
  }, [isOpen, commonTags]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setTags(prev => ({ ...prev, [name]: type === 'number' ? (value ? Number(value) : undefined) : value }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFieldsToUpdate(prev => ({ ...prev, [name as keyof EditableTags]: checked }));
  };

  const handleSave = () => {
    const tagsToApply: Partial<ID3Tags> = {};
    for (const key of editableTagKeys) {
        if (fieldsToUpdate[key]) {
            if (key === 'bitrate' || key === 'sampleRate') {
                tagsToApply[key] = tags[key] || undefined;
            } else {
                tagsToApply[key] = tags[key] || '';
            }
        }
    }
    onSave(tagsToApply);
  };
  
  if (!isOpen) return null;

  const tagLabels: Record<keyof EditableTags, string> = {
      artist: 'Wykonawca',
      albumArtist: 'Wykonawca albumu',
      album: 'Album',
      year: 'Rok',
      genre: 'Gatunek',
      mood: 'Nastrój',
      comments: 'Komentarze',
      bitrate: 'Bitrate (kbps)',
      sampleRate: 'Sample Rate (Hz)',
      composer: 'Kompozytor',
      copyright: 'Prawa autorskie',
      encodedBy: 'Zakodowane przez',
      originalArtist: 'Oryginalny wykonawca',
      discNumber: 'Numer dysku',
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-lg mx-4 transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Edycja masowa ({files.length} plików)</h2>
        <div className="space-y-4">
          {editableTagKeys.map(key => (
            <div key={key} className="flex items-start space-x-3">
              <input 
                type="checkbox"
                id={`update-${key}`}
                name={key}
                checked={fieldsToUpdate[key]}
                onChange={handleCheckboxChange}
                className="h-5 w-5 rounded bg-slate-200 dark:bg-slate-700 border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500 mt-7"
              />
              <div className="flex-grow">
                 <label htmlFor={key} className="block text-sm font-medium text-slate-500 dark:text-slate-400 capitalize">{tagLabels[key]}</label>
                 {key === 'comments' ? (
                      <textarea
                        id={key}
                        name={key}
                        value={tags[key] || ''}
                        onChange={handleChange}
                        placeholder={commonTags[key] === undefined ? '(różne wartości)' : ''}
                        className="mt-1 block w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm py-2 px-3 text-slate-900 dark:text-white focus:outline-none focus:ring-indigo-500 sm:text-sm disabled:opacity-50"
                        disabled={!fieldsToUpdate[key]}
                        rows={2}
                    />
                 ) : (
                    <input
                      type={key === 'bitrate' || key === 'sampleRate' ? 'number' : 'text'}
                      id={key}
                      name={key}
                      value={tags[key] || ''}
                      onChange={handleChange}
                      placeholder={commonTags[key] === undefined ? '(różne wartości)' : ''}
                      className="mt-1 block w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md shadow-sm py-2 px-3 text-slate-900 dark:text-white focus:outline-none focus:ring-indigo-500 sm:text-sm disabled:opacity-50"
                      disabled={!fieldsToUpdate[key]}
                    />
                 )}
              </div>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 dark:text-slate-500 mt-4 text-center">
          Aby wyczyścić tag, zaznacz pole i pozostaw je puste.
        </p>
        <div className="flex justify-end space-x-4 mt-6">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-md hover:bg-slate-200 dark:hover:bg-slate-600">Anuluj</button>
          <button onClick={handleSave} className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500">Zastosuj zmiany</button>
        </div>
      </div>
      <style>{`.animate-fade-in-scale { animation: fade-in-scale 0.2s ease-out forwards; } @keyframes fade-in-scale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }`}</style>
    </div>
  );
};

export default BatchEditModal;