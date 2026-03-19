
import React, { useState, useMemo, useEffect } from 'react';
import { AudioFile, ID3Tags } from '../types';

interface BatchEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (tagsToApply: Partial<ID3Tags>) => void;
  files: AudioFile[];
}

type EditableTags = Pick<ID3Tags, 'artist' | 'albumArtist' | 'album' | 'year' | 'genre' | 'mood' | 'comments' | 'composer' | 'copyright' | 'encodedBy' | 'originalArtist' | 'discNumber'>;
const editableTagKeys: (keyof EditableTags)[] = ['artist', 'albumArtist', 'album', 'year', 'genre', 'composer', 'originalArtist', 'discNumber', 'mood', 'copyright', 'encodedBy', 'comments'];

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
            if (typeof firstValue === 'string' || typeof firstValue === 'undefined') {
                result[key] = firstValue;
            }
        }
    }
    return result;
  }, [files]);

  useEffect(() => {
    if(isOpen) {
        setTags(commonTags);
        setFieldsToUpdate(editableTagKeys.reduce((acc, key) => ({ ...acc, [key]: false }), {} as Record<keyof EditableTags, boolean>));
    }
  }, [isOpen, commonTags]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setTags(prev => ({ ...prev, [name as keyof EditableTags]: value }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFieldsToUpdate(prev => ({ ...prev, [name as keyof EditableTags]: checked }));
  };

  const handleSave = () => {
    const tagsToApply: Partial<ID3Tags> = {};
    for (const key of editableTagKeys) {
        if (fieldsToUpdate[key]) tagsToApply[key] = tags[key] || '';
    }
    onSave(tagsToApply);
  };
  
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="glass-panel w-full max-w-lg rounded-2xl p-6 animate-fade-in-scale max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Edycja masowa ({files.length})</h2>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
        </div>

        <div className="space-y-4">
          {editableTagKeys.map(key => (
            <div key={key} className="flex items-start space-x-3 group">
              <input type="checkbox" id={`update-${key}`} name={key} checked={fieldsToUpdate[key]} onChange={handleCheckboxChange} className="mt-3 h-4 w-4 rounded text-indigo-600 focus:ring-indigo-500 border-slate-300 dark:border-slate-600" />
              <div className="flex-grow">
                 <label htmlFor={key} className={`block text-xs font-semibold uppercase mb-1 transition-colors ${fieldsToUpdate[key] ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'}`}>{key}</label>
                 <input
                    type="text"
                    id={key}
                    name={key}
                    value={tags[key] || ''}
                    onChange={handleChange}
                    placeholder={commonTags[key] === undefined ? '(różne wartości)' : ''}
                    className={`block w-full rounded-lg py-2 px-3 text-sm transition-all outline-none border ${fieldsToUpdate[key] ? 'bg-white dark:bg-slate-800 border-indigo-500 ring-1 ring-indigo-500 text-slate-900 dark:text-white' : 'bg-slate-100 dark:bg-slate-900/50 border-slate-300 dark:border-slate-700 text-slate-500 cursor-not-allowed opacity-60'}`}
                    disabled={!fieldsToUpdate[key]}
                 />
              </div>
            </div>
          ))}
        </div>
        <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">Anuluj</button>
          <button onClick={handleSave} className="px-6 py-2 text-sm font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 shadow-md transition-all active:scale-95">Zastosuj</button>
        </div>
      </div>
    </div>
  );
};

export default BatchEditModal;
