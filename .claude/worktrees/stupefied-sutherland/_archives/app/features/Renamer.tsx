
import React, { useState } from 'react';
import { Icons } from '../Icons';
import { mockFileDatabase } from '../mockData';

export const Renamer = () => {
  const [sourcePaths, setSourcePaths] = useState<string[]>(['/MyMusic']);
  const [namingPattern, setNamingPattern] = useState('{artist} - {title}.{ext}');
  const [slugify, setSlugify] = useState(false);
  const [numbering, setNumbering] = useState(false);
  const [renamePreview, setRenamePreview] = useState<{ originalPath: string, originalName: string, newName: string, conflict?: boolean }[]>([]);
  const [renameHistory, setRenameHistory] = useState<{id: string, timestamp: number, changes: any[]}[]>([]);
  const [renameStatus, setRenameStatus] = useState('');

  const generatePreview = () => {
    const preview = mockFileDatabase.slice(0, 5).map(track => {
      let newName = namingPattern
        .replace('{artist}', track.artist)
        .replace('{title}', track.title)
        .replace('{ext}', track.path.split('.').pop() || 'mp3');
      
      if (slugify) newName = newName.replace(/[^a-z0-9.]/gi, '_').toLowerCase();
      if (numbering) newName = `01_${newName}`;

      return {
        originalPath: track.path,
        originalName: track.path.split('/').pop() || '',
        newName,
        conflict: false
      };
    });
    setRenamePreview(preview);
    setRenameStatus('Preview generated.');
  };

  const startRenaming = () => {
    setRenameStatus('Renaming files (Simulated)...');
    setTimeout(() => {
        const operation = {
            id: Date.now().toString(),
            timestamp: Date.now(),
            changes: [...renamePreview]
        };
        setRenameHistory([...renameHistory, operation]);
        setRenameStatus(`Renaming complete. Processed ${renamePreview.length} files.`);
    }, 1000);
  };

  const undoLastRename = () => {
      if (renameHistory.length === 0) return;
      const lastOp = renameHistory[renameHistory.length - 1];
      setRenameHistory(renameHistory.slice(0, -1));
      setRenameStatus(`Undid last operation (${lastOp.changes.length} files restored).`);
  };

  return (
    <div className="space-y-6">
       <div className="grid grid-cols-2 gap-6">
          <div>
              <label className="block text-sm font-medium mb-1 text-gray-300">Pattern</label>
              <input type="text" value={namingPattern} onChange={e => setNamingPattern(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100" />
              <div className="mt-2 text-xs text-gray-500">Available: {'{artist}, {title}, {album}, {year}, {bpm}, {key}, {ext}'}</div>
          </div>
          <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer mt-6">
                  <input type="checkbox" checked={slugify} onChange={e => setSlugify(e.target.checked)} className="rounded text-blue-500" />
                  <span>Slugify (remove special chars)</span>
              </label>
               <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={numbering} onChange={e => setNumbering(e.target.checked)} className="rounded text-blue-500" />
                  <span>Add Numbering</span>
              </label>
          </div>
       </div>

       <div className="flex gap-3">
          <button onClick={generatePreview} className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition-colors">Generate Preview</button>
          <button onClick={startRenaming} disabled={renamePreview.length === 0} className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded font-semibold transition-colors">Start Renaming</button>
          <button onClick={undoLastRename} disabled={renameHistory.length === 0} className="px-6 py-2 bg-yellow-600 hover:bg-yellow-500 rounded font-semibold transition-colors flex items-center gap-2">
              <Icons.Undo /> Undo
          </button>
       </div>

       {renameStatus && <div className="text-sm text-green-400">{renameStatus}</div>}

       {renamePreview.length > 0 && (
          <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
             <table className="w-full text-sm text-left">
                <thead className="bg-gray-900 text-gray-400 uppercase font-medium">
                   <tr>
                      <th className="px-4 py-2">Original Name</th>
                      <th className="px-4 py-2">New Name</th>
                      <th className="px-4 py-2">Status</th>
                   </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                   {renamePreview.map((item, idx) => (
                      <tr key={idx} className="hover:bg-gray-700/50">
                         <td className="px-4 py-2 text-gray-400">{item.originalName}</td>
                         <td className="px-4 py-2 text-blue-300 font-mono">{item.newName}</td>
                         <td className="px-4 py-2 text-green-500">OK</td>
                      </tr>
                   ))}
                </tbody>
             </table>
          </div>
       )}
    </div>
  );
};
