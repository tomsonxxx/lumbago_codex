import React, { useState, useCallback } from 'react';
import { AudioFile, ID3Tags } from '../types';
import { findDuplicatesByTags, findDuplicatesByHash, DuplicateGroup } from '../utils/duplicateUtils';
import AlbumCover from './AlbumCover';

interface DuplicateFinderModalProps {
  isOpen: boolean;
  onClose: () => void;
  files: AudioFile[];
  onDelete: (fileIds: string[]) => void;
}

type ScanMethod = 'tags' | 'hash';
type ScanStatus = 'idle' | 'scanning' | 'complete';

const DuplicateFinderModal: React.FC<DuplicateFinderModalProps> = ({ isOpen, onClose, files, onDelete }) => {
  const [method, setMethod] = useState<ScanMethod>('tags');
  const [status, setStatus] = useState<ScanStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<DuplicateGroup[]>([]);
  const [selection, setSelection] = useState<Record<string, 'keep' | 'delete'>>({});

  const handleScan = useCallback(async () => {
    setStatus('scanning');
    setProgress(0);
    setResults([]);
    setSelection({});

    const foundDuplicates = method === 'tags'
      ? findDuplicatesByTags(files)
      : await findDuplicatesByHash(files, setProgress);

    setResults(foundDuplicates);
    setStatus('complete');
  }, [method, files]);

  const handleSelectionChange = (groupId: number, fileId: string, action: 'keep' | 'delete') => {
    setSelection(prev => {
      const newSelection = { ...prev };
      // When keeping one, mark all others in the group for deletion
      if (action === 'keep') {
        results[groupId].forEach(file => {
          newSelection[file.id] = file.id === fileId ? 'keep' : 'delete';
        });
      } else { // Just toggle deletion for this one file
        newSelection[fileId] = newSelection[fileId] === 'delete' ? 'keep' : 'delete';
      }
      return newSelection;
    });
  };
  
  const handleAutoSelect = () => {
      const autoSelection: Record<string, 'keep' | 'delete'> = {};
      results.forEach(group => {
          // Logic to decide which file to keep
          // 1. Prefer files with more tags.
          // 2. If tags are equal, prefer larger file size.
          const sortedGroup = [...group].sort((a, b) => {
              const tagsA = a.fetchedTags || a.originalTags;
              const tagsB = b.fetchedTags || b.originalTags;
              const tagCountA = Object.keys(tagsA).length;
              const tagCountB = Object.keys(tagsB).length;

              if (tagCountA !== tagCountB) {
                  return tagCountB - tagCountA; // Higher tag count first
              }
              return b.file.size - a.file.size; // Larger file size first
          });
          
          const fileToKeep = sortedGroup[0];
          group.forEach(file => {
              autoSelection[file.id] = file.id === fileToKeep.id ? 'keep' : 'delete';
          });
      });
      setSelection(autoSelection);
  };

  const handleDelete = () => {
    const idsToDelete = Object.entries(selection)
      .filter(([, action]) => action === 'delete')
      .map(([id]) => id);
    
    if (idsToDelete.length > 0) {
      onDelete(idsToDelete);
    }
    onClose();
  };
  
  const resetState = () => {
      setStatus('idle');
      setProgress(0);
      setResults([]);
      setSelection({});
  }

  if (!isOpen) return null;
  
  const filesToDeleteCount = Object.values(selection).filter(v => v === 'delete').length;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-4xl mx-4 max-h-[90vh] flex flex-col transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-white mb-4">Wyszukiwarka Duplikatów</h2>
        
        {status === 'idle' && (
            <div className="flex flex-col items-center justify-center h-full">
                <p className="text-slate-300 mb-4">Wybierz metodę wyszukiwania duplikatów:</p>
                <div className="flex space-x-4 mb-6">
                    <button onClick={() => setMethod('tags')} className={`px-4 py-2 rounded-md ${method === 'tags' ? 'bg-indigo-600 text-white' : 'bg-slate-700 hover:bg-slate-600'}`}>Według tagów (szybko)</button>
                    <button onClick={() => setMethod('hash')} className={`px-4 py-2 rounded-md ${method === 'hash' ? 'bg-indigo-600 text-white' : 'bg-slate-700 hover:bg-slate-600'}`}>Według sumy kontrolnej (dokładnie)</button>
                </div>
                 <p className="text-xs text-slate-400 text-center max-w-md">
                    <b>Według tagów:</b> Porównuje tytuł i artystę. Szybkie, ale może pominąć duplikaty o różnych tagach.
                    <br/>
                    <b>Według sumy kontrolnej:</b> Porównuje zawartość plików bit po bicie. 100% dokładne, ale wolniejsze dla dużej liczby plików.
                 </p>
            </div>
        )}

        {status === 'scanning' && (
            <div className="flex flex-col items-center justify-center h-full">
                <p className="text-lg text-slate-300 mb-4">Skanowanie w toku...</p>
                <div className="w-full bg-slate-700 rounded-full h-2.5">
                    <div className="bg-indigo-600 h-2.5 rounded-full" style={{ width: `${progress * 100}%` }}></div>
                </div>
                <p className="text-sm text-slate-400 mt-2">Przetworzono {Math.round(progress * files.length)} z {files.length} plików</p>
            </div>
        )}
        
        {status === 'complete' && (
            <div className="flex flex-col flex-grow min-h-0">
                <div className="flex justify-between items-center mb-4">
                     <p className="text-slate-300">Znaleziono {results.length} {results.length === 1 ? 'grupę' : 'grup'} duplikatów.</p>
                     <button onClick={handleAutoSelect} className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 rounded-md">Auto-wybierz</button>
                </div>
                <div className="flex-grow overflow-y-auto pr-2">
                    {results.map((group, groupIndex) => (
                        <div key={groupIndex} className="bg-slate-900/50 rounded-lg p-3 mb-3">
                            <h3 className="font-bold text-indigo-400 mb-2">Grupa {groupIndex + 1}</h3>
                            {group.map(file => {
                                const tags = file.fetchedTags || file.originalTags;
                                return (
                                <div key={file.id} className="flex items-center justify-between p-2 rounded-md hover:bg-slate-700/50">
                                    <div className="flex items-center gap-3">
                                        <AlbumCover tags={tags} className="w-10 h-10" />
                                        <div>
                                            <p className="font-semibold text-sm">{tags.artist} - {tags.title}</p>
                                            <p className="text-xs text-slate-400 truncate max-w-md" title={file.webkitRelativePath || file.file.name}>{file.webkitRelativePath || file.file.name}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <button onClick={() => handleSelectionChange(groupIndex, file.id, 'keep')} className={`px-3 py-1 text-xs rounded ${selection[file.id] === 'keep' ? 'bg-green-600 text-white' : 'bg-slate-600'}`}>Zachowaj</button>
                                        <button onClick={() => handleSelectionChange(groupIndex, file.id, 'delete')} className={`px-3 py-1 text-xs rounded ${selection[file.id] === 'delete' ? 'bg-red-600 text-white' : 'bg-slate-600'}`}>Usuń</button>
                                    </div>
                                </div>
                            )})}
                        </div>
                    ))}
                </div>
            </div>
        )}

        <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-700">
            {status === 'complete' && <button onClick={resetState} className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700 rounded-md hover:bg-slate-600">Powrót</button>}
            {status !== 'scanning' && <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700 rounded-md hover:bg-slate-600">Anuluj</button>}
            
            {status === 'idle' && <button onClick={handleScan} className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500">Rozpocznij skanowanie</button>}
            {status === 'complete' && <button onClick={handleDelete} disabled={filesToDeleteCount === 0} className="px-4 py-2 text-sm font-bold text-white bg-red-600 rounded-md hover:bg-red-500 disabled:bg-red-400 disabled:cursor-not-allowed">Usuń zaznaczone ({filesToDeleteCount})</button>}
        </div>

        <style>{`.animate-fade-in-scale { animation: fade-in-scale 0.2s ease-out forwards; } @keyframes fade-in-scale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }`}</style>
      </div>
    </div>
  );
};

export default DuplicateFinderModal;
