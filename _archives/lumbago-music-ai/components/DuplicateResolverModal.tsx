
import React, { useState, useMemo } from 'react';
import { AudioFile } from '../types';

interface DuplicateResolverModalProps {
  isOpen: boolean;
  onClose: () => void;
  duplicateSets: Map<string, AudioFile[]>;
  onRemoveFiles: (fileIds: string[]) => void;
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const DuplicateResolverModal: React.FC<DuplicateResolverModalProps> = ({
  isOpen,
  onClose,
  duplicateSets,
  onRemoveFiles,
}) => {
  const [selectedForDeletion, setSelectedForDeletion] = useState<Set<string>>(new Set());
  const sets = useMemo(() => Array.from(duplicateSets.entries()), [duplicateSets]);

  const toggleSelection = (id: string) => {
    const newSet = new Set(selectedForDeletion);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedForDeletion(newSet);
  };

  const handleAutoSelect = () => {
    const newSelection = new Set<string>();
    sets.forEach(([_, files]) => {
      // Sort by quality (bitrate/size) - keep the best one
      const sorted = [...files].sort((a, b) => {
        const bitrateA = (a.fetchedTags?.bitrate || a.originalTags?.bitrate || 0);
        const bitrateB = (b.fetchedTags?.bitrate || b.originalTags?.bitrate || 0);
        if (bitrateB !== bitrateA) return bitrateB - bitrateA;
        return b.file.size - a.file.size;
      });
      // Mark all except the first (best) for deletion
      for (let i = 1; i < sorted.length; i++) newSelection.add(sorted[i].id);
    });
    setSelectedForDeletion(newSelection);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div 
        className="glass-panel flex flex-col w-full max-w-5xl h-[85vh] rounded-2xl animate-fade-in-scale overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center bg-slate-50/50 dark:bg-slate-800/30">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Duplikaty</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">Znaleziono {sets.length} grup. Wybierz pliki do usunięcia.</p>
          </div>
          <button 
            onClick={handleAutoSelect}
            className="px-4 py-2 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 rounded-lg text-sm font-semibold hover:bg-indigo-200 dark:hover:bg-indigo-900/50 transition-colors flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" /></svg>
            Auto-zaznacz gorsze
          </button>
        </div>

        <div className="flex-grow overflow-y-auto p-6 space-y-6 bg-slate-50/30 dark:bg-slate-900/30">
          {sets.map(([setId, files]) => (
            <div key={setId} className="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
              <div className="bg-slate-100/50 dark:bg-slate-800 px-4 py-2 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200 dark:border-slate-700 flex justify-between">
                 <span>Grupa Duplikatów</span>
                 <span>{files.length} pliki</span>
              </div>
              <table className="w-full text-left text-sm">
                <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                  {files.map(file => {
                    const isMarked = selectedForDeletion.has(file.id);
                    const bitrate = file.fetchedTags?.bitrate || file.originalTags?.bitrate;
                    return (
                      <tr key={file.id} className={`transition-colors ${isMarked ? 'bg-red-50 dark:bg-red-900/10' : 'hover:bg-slate-50 dark:hover:bg-slate-700/30'}`}>
                        <td className="px-4 py-3 w-10">
                          <input type="checkbox" checked={isMarked} onChange={() => toggleSelection(file.id)} className="h-4 w-4 rounded text-red-600 focus:ring-red-500 border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700" />
                        </td>
                        <td className="px-4 py-3">
                          <div className={`font-medium ${isMarked ? 'text-slate-500 line-through decoration-red-500' : 'text-slate-900 dark:text-slate-200'}`}>{file.file.name}</div>
                          <div className="text-xs text-slate-500 truncate max-w-xs" title={file.webkitRelativePath}>{file.webkitRelativePath}</div>
                        </td>
                        <td className="px-4 py-3 text-slate-500 font-mono text-xs">{bitrate ? `${Math.round(bitrate / 1000)} kbps` : '-'}</td>
                        <td className="px-4 py-3 text-slate-500 font-mono text-xs">{formatSize(file.file.size)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ))}
        </div>

        <div className="p-6 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex justify-between items-center">
          <div className="text-sm text-slate-500">Do usunięcia: <strong className="text-red-600 dark:text-red-400">{selectedForDeletion.size}</strong> plików</div>
          <div className="space-x-3">
            <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">Anuluj</button>
            <button onClick={() => { onRemoveFiles(Array.from(selectedForDeletion)); onClose(); }} disabled={selectedForDeletion.size === 0} className="px-5 py-2 text-sm font-bold text-white bg-red-600 rounded-lg hover:bg-red-500 disabled:opacity-50 shadow-md transition-all active:scale-95">Usuń zaznaczone</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DuplicateResolverModal;
