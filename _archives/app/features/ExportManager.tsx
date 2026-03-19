
import React, { useState } from 'react';
import { mockFileDatabase } from '../mockData';
import { Icons } from '../Icons';

export const ExportManager = () => {
    const [targetDevice, setTargetDevice] = useState('USB DISK (E:)');
    const [exportFormat, setExportFormat] = useState<'cdj' | 'generic' | 'm3u'>('cdj');
    const [transcode, setTranscode] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [progress, setProgress] = useState(0);
    const [log, setLog] = useState<string[]>([]);

    const startExport = async () => {
        setIsExporting(true);
        setLog([]);
        setProgress(0);

        const tracksToExport = mockFileDatabase.slice(0, 5); // Simulate top 5 tracks
        const total = tracksToExport.length;

        setLog(prev => [...prev, `Initializing export to ${targetDevice}...`]);
        setLog(prev => [...prev, `Format: ${exportFormat.toUpperCase()}, Transcode: ${transcode ? 'ON' : 'OFF'}`]);
        
        for (let i = 0; i < total; i++) {
            const track = tracksToExport[i];
            
            // Simulate processing time
            await new Promise(r => setTimeout(r, 800));
            
            setLog(prev => [...prev, `[${i+1}/${total}] Copying: ${track.artist} - ${track.title}`]);
            if (transcode && track.path.endsWith('.flac')) {
                setLog(prev => [...prev, `   ↳ Transcoding FLAC to MP3 320kbps...`]);
            }
            if (exportFormat === 'cdj') {
                setLog(prev => [...prev, `   ↳ Generating Rekordbox analysis files (PIONEER)...`]);
            }

            setProgress(Math.round(((i + 1) / total) * 100));
        }

        setLog(prev => [...prev, 'Export Completed Successfully!']);
        setLog(prev => [...prev, 'Safe to eject device.']);
        setIsExporting(false);
    };

    return (
        <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-400">
                        <Icons.Share width={28} height={28} />
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-gray-200">Export Manager</h3>
                        <p className="text-sm text-gray-400">Prepare USB drives for CDJs, XDJs, or car audio.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Settings */}
                    <div className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-300">Target Device</label>
                            <select 
                                value={targetDevice}
                                onChange={e => setTargetDevice(e.target.value)}
                                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100"
                            >
                                <option value="USB DISK (E:)">USB DISK (E:) - 32GB FAT32</option>
                                <option value="SD CARD (F:)">SD CARD (F:) - 64GB exFAT</option>
                                <option value="Local Folder">Local Folder (For Testing)</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2 text-gray-300">Export Structure</label>
                            <div className="grid grid-cols-1 gap-2">
                                <label className={`flex items-center gap-3 p-3 rounded border cursor-pointer ${exportFormat === 'cdj' ? 'bg-blue-900/20 border-blue-500' : 'bg-gray-900 border-gray-700'}`}>
                                    <input type="radio" name="fmt" checked={exportFormat === 'cdj'} onChange={() => setExportFormat('cdj')} />
                                    <div>
                                        <div className="font-bold text-gray-200">CDJ / Rekordbox</div>
                                        <div className="text-xs text-gray-500">PIONEER folder structure with analysis files</div>
                                    </div>
                                </label>
                                <label className={`flex items-center gap-3 p-3 rounded border cursor-pointer ${exportFormat === 'generic' ? 'bg-blue-900/20 border-blue-500' : 'bg-gray-900 border-gray-700'}`}>
                                    <input type="radio" name="fmt" checked={exportFormat === 'generic'} onChange={() => setExportFormat('generic')} />
                                    <div>
                                        <div className="font-bold text-gray-200">Generic USB</div>
                                        <div className="text-xs text-gray-500">Artist/Album folder structure</div>
                                    </div>
                                </label>
                                <label className={`flex items-center gap-3 p-3 rounded border cursor-pointer ${exportFormat === 'm3u' ? 'bg-blue-900/20 border-blue-500' : 'bg-gray-900 border-gray-700'}`}>
                                    <input type="radio" name="fmt" checked={exportFormat === 'm3u'} onChange={() => setExportFormat('m3u')} />
                                    <div>
                                        <div className="font-bold text-gray-200">M3U Playlist Only</div>
                                        <div className="text-xs text-gray-500">Relative paths m3u file</div>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <div>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    checked={transcode} 
                                    onChange={e => setTranscode(e.target.checked)} 
                                    className="rounded text-blue-500 w-5 h-5"
                                />
                                <span className="text-gray-300">Convert lossless (FLAC/WAV) to MP3 320kbps</span>
                            </label>
                            <p className="text-xs text-gray-500 mt-1 ml-7">Required for older CDJ models (CDJ-900, CDJ-2000 non-NXS)</p>
                        </div>

                        <button 
                            onClick={startExport}
                            disabled={isExporting}
                            className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded font-bold shadow-lg shadow-blue-900/50 transition-all active:scale-95 disabled:opacity-50"
                        >
                            {isExporting ? 'Exporting...' : 'Start Export'}
                        </button>
                    </div>

                    {/* Status & Log */}
                    <div className="bg-black/40 rounded-lg p-4 font-mono text-xs flex flex-col">
                        <div className="mb-2 flex justify-between text-gray-400 uppercase font-bold tracking-wider">
                            <span>Process Log</span>
                            <span>{progress}%</span>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto space-y-1 mb-4 h-64 scrollbar-thin scrollbar-thumb-gray-700">
                            {log.length === 0 && <div className="text-gray-600 italic">Waiting to start...</div>}
                            {log.map((entry, i) => (
                                <div key={i} className={`break-words ${entry.includes('Error') ? 'text-red-400' : 'text-green-400'}`}>
                                    {'>'} {entry}
                                </div>
                            ))}
                        </div>

                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                            <div 
                                className="h-full bg-blue-500 transition-all duration-300"
                                style={{ width: `${progress}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
