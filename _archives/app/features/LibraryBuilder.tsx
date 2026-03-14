
import React, { useState } from 'react';
import { mockFileDatabase } from '../mockData';

export const LibraryBuilder = () => {
    const [sourcePaths, setSourcePaths] = useState<string[]>([]);
    const [sourcePathsInput, setSourcePathsInput] = useState('');
    const [destinationPath, setDestinationPath] = useState('/New_DJ_Library');
    const [folderTemplate, setFolderTemplate] = useState('{genre}/{year}/{artist}/{album}');
    const [actionType, setActionType] = useState<'copy' | 'move'>('copy');
    const [createDB, setCreateDB] = useState(true);
    const [filterCriteria, setFilterCriteria] = useState('');
    const [isBuilding, setIsBuilding] = useState(false);
    const [buildStatus, setBuildStatus] = useState('');
    const [simulatedStructure, setSimulatedStructure] = useState<{ original: string, newPath: string }[]>([]);

    const handleSourcePathsChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setSourcePathsInput(e.target.value);
        setSourcePaths(e.target.value.split('\n').filter(p => p.trim() !== ''));
    };

    const startDryRun = async () => {
        setBuildStatus('Generating dry run preview...');
        setSimulatedStructure([]);
        
        await new Promise(resolve => setTimeout(resolve, 800));

        const preview: { original: string, newPath: string }[] = [];
        
        const filteredFiles = mockFileDatabase.filter(file => {
            if (!filterCriteria) return true;
            const [key, val] = filterCriteria.split(':');
            if (key && val && (file as any)[key.trim().toLowerCase()]) {
                return String((file as any)[key.trim().toLowerCase()]).toLowerCase().includes(val.trim().toLowerCase());
            }
            return true;
        });

        filteredFiles.forEach(file => {
            let newPath = folderTemplate;
            newPath = newPath.replace('{genre}', file.genre);
            newPath = newPath.replace('{year}', file.year);
            newPath = newPath.replace('{artist}', file.artist);
            newPath = newPath.replace('{album}', file.album);
            newPath = `${destinationPath}/${newPath}/${file.path.split('/').pop()}`.replace(/\/\//g, '/');
            preview.push({ original: file.path, newPath });
        });

        setSimulatedStructure(preview);
        setBuildStatus(`Dry run complete. ${preview.length} files to process.`);
    };

    const buildLibrary = async () => {
        if (simulatedStructure.length === 0) return;
        setIsBuilding(true);
        setBuildStatus('Starting library build...');

        for (let i = 0; i <= 100; i += 10) {
            setBuildStatus(`Building library... ${i}%`);
            await new Promise(resolve => setTimeout(resolve, 200));
        }

        setBuildStatus('Library build complete (Simulated)!');
        setIsBuilding(false);
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
                <div>
                    <label className="block text-sm font-medium mb-1 text-gray-300">Source Paths (One per line)</label>
                    <textarea 
                        value={sourcePathsInput}
                        onChange={handleSourcePathsChange}
                        placeholder="/Path/To/Source1&#10;/Path/To/Source2"
                        className="w-full h-32 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100 text-sm font-mono"
                    />
                </div>
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1 text-gray-300">Destination Path</label>
                        <input type="text" value={destinationPath} onChange={e => setDestinationPath(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1 text-gray-300">Folder Structure Template</label>
                        <input type="text" value={folderTemplate} onChange={e => setFolderTemplate(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100" />
                    </div>
                    <div>
                         <label className="block text-sm font-medium mb-1 text-gray-300">Filter Criteria (Optional)</label>
                         <input type="text" value={filterCriteria} onChange={e => setFilterCriteria(e.target.value)} placeholder="e.g. genre:House" className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100" />
                    </div>
                </div>
            </div>

            <div className="flex gap-6 items-center bg-gray-800/50 p-4 rounded-lg border border-gray-700">
                <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input type="radio" name="actionType" checked={actionType === 'copy'} onChange={() => setActionType('copy')} className="text-blue-500" />
                        <span>Copy Files</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input type="radio" name="actionType" checked={actionType === 'move'} onChange={() => setActionType('move')} className="text-blue-500" />
                        <span>Move Files</span>
                    </label>
                </div>
                <label className="flex items-center gap-2 cursor-pointer ml-auto">
                    <input type="checkbox" checked={createDB} onChange={e => setCreateDB(e.target.checked)} className="rounded text-blue-500" />
                    <span>Create SQLite DB</span>
                </label>
            </div>

            <div className="flex gap-3">
                <button onClick={startDryRun} className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded font-semibold transition-colors">Start Dry Run</button>
                <button onClick={buildLibrary} disabled={isBuilding || simulatedStructure.length === 0} className={`px-6 py-2 rounded font-semibold transition-colors ${isBuilding || simulatedStructure.length === 0 ? 'bg-gray-800 text-gray-500 cursor-not-allowed' : 'bg-green-600 hover:bg-green-500'}`}>Build Library</button>
            </div>

            {buildStatus && <div className="text-sm text-blue-300 font-mono">{buildStatus}</div>}

            {simulatedStructure.length > 0 && (
                <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
                    <div className="px-4 py-2 bg-gray-900 border-b border-gray-700 font-semibold text-sm">Simulated Output Structure</div>
                    <div className="max-h-60 overflow-y-auto p-2 space-y-1">
                        {simulatedStructure.map((item, idx) => (
                            <div key={idx} className="text-xs font-mono grid grid-cols-2 gap-4 hover:bg-gray-700/50 p-1 rounded">
                                <span className="text-gray-400 truncate" title={item.original}>{item.original}</span>
                                <span className="text-green-400 truncate" title={item.newPath}>→ {item.newPath}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
