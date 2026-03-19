
import React, { useState } from 'react';
import { mockFileDatabase } from '../mockData';

export const DuplicateFinder = () => {
    const [detectionMethod, setDetectionMethod] = useState<'fingerprint' | 'hash' | 'tags'>('fingerprint');
    const [scanPathsInput, setScanPathsInput] = useState('/MyMusic');
    const [similarityThreshold, setSimilarityThreshold] = useState(0.95);
    const [duplicateGroups, setDuplicateGroups] = useState<any[]>([]);
    const [isFinding, setIsFinding] = useState(false);
    const [scanStatus, setScanStatus] = useState('');

    const findDuplicates = async () => {
        setIsFinding(true);
        setScanStatus('Scanning for duplicates (Simulated)...');
        setDuplicateGroups([]);
        
        await new Promise(resolve => setTimeout(resolve, 1500));

        const groups = [];
        if (detectionMethod === 'fingerprint' || detectionMethod === 'hash') {
             const group1 = mockFileDatabase.filter(f => f.hash === 'h123A');
             if (group1.length > 1) groups.push({ id: 'g1', files: group1, score: 1.0 });
             
             const group2 = mockFileDatabase.filter(f => f.hash === 'h123B');
             if (group2.length > 1) groups.push({ id: 'g2', files: group2, score: 0.98 });
        } else {
             const group3 = mockFileDatabase.filter(f => f.title === 'Track 1');
             if (group3.length > 1) groups.push({ id: 'g3', files: group3, score: 1.0 });
        }

        setDuplicateGroups(groups);
        setScanStatus(`Found ${groups.length} groups of duplicates.`);
        setIsFinding(false);
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-3 gap-6">
                 <div className="col-span-1 space-y-4">
                    <label className="block text-sm font-medium mb-1 text-gray-300">Method</label>
                    <div className="space-y-2">
                        <label className="flex items-center gap-2 cursor-pointer bg-gray-800 p-2 rounded border border-gray-700">
                            <input type="radio" name="detMethod" checked={detectionMethod === 'fingerprint'} onChange={() => setDetectionMethod('fingerprint')} />
                            <span>Audio Fingerprint</span>
                        </label>
                         <label className="flex items-center gap-2 cursor-pointer bg-gray-800 p-2 rounded border border-gray-700">
                            <input type="radio" name="detMethod" checked={detectionMethod === 'hash'} onChange={() => setDetectionMethod('hash')} />
                            <span>Hash / Checksum</span>
                        </label>
                         <label className="flex items-center gap-2 cursor-pointer bg-gray-800 p-2 rounded border border-gray-700">
                            <input type="radio" name="detMethod" checked={detectionMethod === 'tags'} onChange={() => setDetectionMethod('tags')} />
                            <span>Tag-based</span>
                        </label>
                    </div>
                 </div>
                 <div className="col-span-2 space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1 text-gray-300">Scan Paths</label>
                         <input type="text" value={scanPathsInput} onChange={e => setScanPathsInput(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100" />
                    </div>
                    {detectionMethod === 'fingerprint' && (
                         <div>
                            <label className="block text-sm font-medium mb-1 text-gray-300">Similarity Threshold: {Math.round(similarityThreshold * 100)}%</label>
                            <input type="range" min="0.8" max="1.0" step="0.01" value={similarityThreshold} onChange={e => setSimilarityThreshold(parseFloat(e.target.value))} className="w-full" />
                         </div>
                    )}
                 </div>
            </div>

            <div className="flex gap-3">
                 <button onClick={findDuplicates} disabled={isFinding} className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded font-semibold transition-colors flex-1">
                    {isFinding ? 'Scanning...' : 'Find Duplicates'}
                 </button>
            </div>
            
            {scanStatus && <div className="text-sm text-gray-400">{scanStatus}</div>}

            <div className="space-y-4">
                {duplicateGroups.map(group => (
                    <div key={group.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-3">
                            <span className="font-semibold text-red-300">Duplicate Group (Score: {Math.round(group.score * 100)}%)</span>
                            <div className="space-x-2">
                                <button className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded">Auto-Resolve</button>
                            </div>
                        </div>
                        <ul className="space-y-2">
                            {group.files.map((file: any, idx: number) => (
                                <li key={idx} className="flex justify-between items-center bg-gray-900/50 p-2 rounded text-sm">
                                    <div className="flex flex-col">
                                        <span className="text-gray-200">{file.title} - {file.artist}</span>
                                        <span className="text-xs text-gray-500 font-mono">{file.path}</span>
                                    </div>
                                    <div className="flex gap-2">
                                        <button className="text-xs text-green-400 hover:underline">Keep</button>
                                        <button className="text-xs text-red-400 hover:underline">Delete</button>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div>
    );
};
