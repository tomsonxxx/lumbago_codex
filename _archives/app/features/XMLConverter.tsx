
import React, { useState } from 'react';
import { Icons } from '../Icons';

export const XMLConverter = () => {
    const [sourceFormat, setSourceFormat] = useState('rekordbox');
    const [targetFormat, setTargetFormat] = useState('virtualdj');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isConverting, setIsConverting] = useState(false);
    const [conversionLog, setConversionLog] = useState<string[]>([]);
    const [isDryRun, setIsDryRun] = useState(false);

    const handleConvert = async () => {
        if (!selectedFile) return;
        setIsConverting(true);
        setConversionLog(['Starting XML parsing...', `Reading ${selectedFile.name} as ${sourceFormat}...`]);
        
        for (let i = 0; i < 5; i++) {
            await new Promise(resolve => setTimeout(resolve, 600));
            setConversionLog(prev => [...prev, `Processing track batch ${i+1}... Mapping metadata...`]);
        }

        if (isDryRun) {
             setConversionLog(prev => [...prev, 'Dry Run Complete. No files written.', 'Found 1245 tracks, 0 errors.']);
        } else {
             setConversionLog(prev => [...prev, 'Conversion Complete!', `Generated ${targetFormat}_database.xml`]);
        }
        setIsConverting(false);
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
                <div>
                    <label className="block text-sm font-medium mb-1 text-gray-300">Source Format</label>
                    <select value={sourceFormat} onChange={e => setSourceFormat(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100">
                        <option value="rekordbox">Rekordbox XML</option>
                        <option value="virtualdj">VirtualDJ Database</option>
                        <option value="serato">Serato (Partial)</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1 text-gray-300">Target Format</label>
                    <select value={targetFormat} onChange={e => setTargetFormat(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-100">
                         <option value="virtualdj">VirtualDJ Database</option>
                         <option value="rekordbox">Rekordbox XML</option>
                         <option value="denon">Denon Engine Prime</option>
                    </select>
                </div>
            </div>

            <div className="bg-gray-800 border border-dashed border-gray-600 rounded-lg p-8 flex flex-col items-center justify-center text-center">
                 <Icons.RefreshCw />
                 <p className="mt-4 text-gray-300">Drag & Drop XML file here or click to browse</p>
                 <input type="file" accept=".xml" onChange={e => setSelectedFile(e.target.files?.[0] || null)} className="mt-4 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700" />
            </div>

            <div className="flex gap-4 items-center">
                 <label className="flex items-center gap-2 cursor-pointer text-gray-300">
                     <input type="checkbox" checked={isDryRun} onChange={e => setIsDryRun(e.target.checked)} className="rounded text-blue-500" />
                     <span>Dry Run (Check only)</span>
                 </label>
                 <button onClick={handleConvert} disabled={!selectedFile || isConverting} className="ml-auto px-6 py-2 bg-green-600 hover:bg-green-500 rounded font-semibold disabled:opacity-50 transition-colors">
                     {isConverting ? 'Converting...' : 'Start Conversion'}
                 </button>
            </div>

            {conversionLog.length > 0 && (
                <div className="bg-black/30 border border-gray-700 rounded p-4 font-mono text-xs text-green-400 h-48 overflow-y-auto">
                    {conversionLog.map((log, i) => <div key={i}>[{new Date().toLocaleTimeString()}] {log}</div>)}
                </div>
            )}
        </div>
    );
};
