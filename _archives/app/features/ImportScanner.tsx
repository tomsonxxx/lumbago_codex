
import React, { useState, useRef, useEffect } from 'react';
import { Icons } from '../Icons';
import { normalizePath, globToRegex } from '../utils';
import { db } from '../db';

export const ImportScanner = () => {
  // Configuration
  const [includePatterns, setIncludePatterns] = useState('*.{mp3,flac,m4a,wav,aac,dsf,aiff,ogg}');
  const [excludePatterns, setExcludePatterns] = useState('*_backup*, *.txt, *.log, .DS_Store');
  
  // State
  const [isScanning, setIsScanning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [scanLog, setScanLog] = useState<string[]>([]);
  const [stats, setStats] = useState({ total: 0, success: 0, skipped: 0, errors: 0 });
  const [dbCount, setDbCount] = useState(0);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const processingRef = useRef<{ paused: boolean, stop: boolean }>({ paused: false, stop: false });
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Load initial DB stats
  useEffect(() => {
    db.tracks.count().then(setDbCount);
  }, []);

  // Auto-scroll log
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [scanLog]);

  const addLog = (msg: string, type: 'info' | 'success' | 'error' | 'system' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setScanLog(prev => [...prev.slice(-99), `[${timestamp}] [${type.toUpperCase()}] ${msg}`]);
  };

  const checkPatterns = (fileName: string): { allowed: boolean; reason?: string } => {
    try {
      const excludes = excludePatterns.split(',').map(p => p.trim()).filter(Boolean);
      for (const pattern of excludes) {
        if (globToRegex(pattern).test(fileName)) {
          return { allowed: false, reason: `Matches exclude pattern: ${pattern}` };
        }
      }

      const includes = includePatterns.split(',').map(p => p.trim()).filter(Boolean);
      if (includes.length === 0) return { allowed: true };

      const isIncluded = includes.some(pattern => globToRegex(pattern).test(fileName));
      if (!isIncluded) {
        return { allowed: false, reason: 'Does not match include pattern' };
      }

      return { allowed: true };
    } catch (e) {
      return { allowed: false, reason: 'Invalid Glob Pattern' };
    }
  };

  // Helper to get duration from audio file
  const getAudioMetadata = (file: File): Promise<{ duration: number }> => {
    return new Promise((resolve) => {
      const audio = new Audio(URL.createObjectURL(file));
      audio.onloadedmetadata = () => {
        URL.revokeObjectURL(audio.src);
        resolve({ duration: audio.duration });
      };
      audio.onerror = () => {
        resolve({ duration: 0 });
      };
    });
  };

  const handleFolderSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    // Reset State
    setIsScanning(true);
    setIsPaused(false);
    processingRef.current = { paused: false, stop: false };
    setProgress(0);
    setScanLog([]);
    setStats({ total: files.length, success: 0, skipped: 0, errors: 0 });

    addLog(`Selected directory containing ${files.length} files. Starting scan...`, 'system');

    // Convert FileList to Array for processing
    const fileArray = Array.from(files);
    const totalFiles = fileArray.length;

    for (let i = 0; i < totalFiles; i++) {
        // Check control flags
        if (processingRef.current.stop) break;
        
        while (processingRef.current.paused) {
            await new Promise(r => setTimeout(r, 500));
            if (processingRef.current.stop) break;
        }

        const file = fileArray[i];
        const relativePath = file.webkitRelativePath || file.name;
        
        setCurrentFile(relativePath);
        
        // 1. Pattern Matching
        const { allowed, reason } = checkPatterns(file.name);
        
        if (allowed) {
            try {
                addLog(`Processing: ${file.name}`, 'info');
                
                // 2. Metadata Extraction (Real)
                const meta = await getAudioMetadata(file);
                
                // 3. Save to DB
                await db.tracks.add({
                    path: relativePath, // Storing relative path as browser obscures full path
                    title: file.name.replace(/\.[^/.]+$/, ""),
                    artist: 'Unknown Artist', // Requires ID3 parser lib for real value
                    album: 'Unknown Album',
                    genre: 'Unknown',
                    year: '',
                    bpm: 0,
                    key: '',
                    duration: meta.duration,
                    fileSize: file.size,
                    format: file.name.split('.').pop()?.toLowerCase() || 'unknown',
                    dateAdded: Date.now()
                });

                setStats(prev => ({ ...prev, success: prev.success + 1 }));
                addLog(`Imported: ${file.name}`, 'success');
            } catch (err) {
                console.error(err);
                setStats(prev => ({ ...prev, errors: prev.errors + 1 }));
                addLog(`Error processing ${file.name}`, 'error');
            }
        } else {
            setStats(prev => ({ ...prev, skipped: prev.skipped + 1 }));
        }

        setProgress(Math.round(((i + 1) / totalFiles) * 100));
        
        // Yield to UI to prevent freezing
        if (i % 5 === 0) await new Promise(r => setTimeout(r, 0));
    }

    setIsScanning(false);
    setCurrentFile('');
    addLog("Scanning session completed.", 'system');
    
    // Refresh DB count
    db.tracks.count().then(setDbCount);
  };

  const togglePause = () => {
    processingRef.current.paused = !processingRef.current.paused;
    setIsPaused(processingRef.current.paused);
    addLog(processingRef.current.paused ? "Paused scanning." : "Resumed scanning.", 'system');
  };

  const stopScan = () => {
    processingRef.current.stop = true;
    addLog("Stopping scan...", 'error');
  };

  return (
    <div className="flex flex-col h-full gap-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Configuration */}
        <div className="lg:col-span-2 space-y-4">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                    <div className="p-3 bg-blue-900/30 rounded-lg text-blue-400">
                        <Icons.FolderInput width={24} height={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-gray-200">Local Directory Scanner</h3>
                        <p className="text-sm text-gray-400">Select a folder on your computer to recursively scan for audio files.</p>
                    </div>
                </div>

                <div className="flex gap-4 items-center">
                    <button 
                        onClick={() => fileInputRef.current?.click()} 
                        disabled={isScanning && !isPaused}
                        className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded font-bold text-white shadow-lg shadow-blue-900/50 transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2"
                    >
                        <Icons.FolderInput /> Select Directory
                    </button>
                    <span className="text-sm text-gray-500">
                        {stats.total > 0 ? `Selected ${stats.total} files` : 'No directory selected'}
                    </span>
                    {/* Hidden input for folder selection */}
                    <input 
                        type="file" 
                        ref={fileInputRef}
                        onChange={handleFolderSelect}
                        // @ts-ignore - webkitdirectory is non-standard but supported in modern browsers
                        webkitdirectory="" 
                        directory="" 
                        multiple 
                        className="hidden"
                    />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                    <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Include Formats</label>
                    <input 
                        type="text" 
                        value={includePatterns}
                        onChange={(e) => setIncludePatterns(e.target.value)}
                        className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-green-400 font-mono"
                        disabled={isScanning}
                    />
                </div>
                <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                    <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Exclude Patterns</label>
                    <input 
                        type="text" 
                        value={excludePatterns}
                        onChange={(e) => setExcludePatterns(e.target.value)}
                        className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-red-400 font-mono"
                        disabled={isScanning}
                    />
                </div>
            </div>
        </div>

        {/* Stats Panel */}
        <div className="bg-gray-800 p-5 rounded-lg border border-gray-700 shadow-sm flex flex-col justify-between">
            <div>
                <h3 className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-4">Live Statistics</h3>
                <div className="space-y-3">
                     <div className="flex justify-between items-center">
                        <span className="text-gray-300">Total Scanned</span>
                        <span className="font-mono font-bold text-white">{stats.total}</span>
                     </div>
                     <div className="flex justify-between items-center">
                        <span className="text-gray-300">Imported to DB</span>
                        <span className="font-mono font-bold text-green-400">{stats.success}</span>
                     </div>
                     <div className="flex justify-between items-center">
                        <span className="text-gray-300">Skipped</span>
                        <span className="font-mono font-bold text-yellow-500">{stats.skipped}</span>
                     </div>
                     <div className="flex justify-between items-center">
                        <span className="text-gray-300">Errors</span>
                        <span className="font-mono font-bold text-red-500">{stats.errors}</span>
                     </div>
                     <div className="pt-4 mt-4 border-t border-gray-700 flex justify-between items-center">
                        <span className="text-gray-400 font-bold">Total in Library</span>
                        <span className="font-mono font-bold text-blue-400">{dbCount}</span>
                     </div>
                </div>
            </div>

            {isScanning && (
                <div className="flex gap-2 mt-6">
                     <button 
                        onClick={togglePause} 
                        className={`flex-1 py-2 rounded font-bold text-white transition-colors ${isPaused ? 'bg-green-600 hover:bg-green-500' : 'bg-yellow-600 hover:bg-yellow-500'}`}
                    >
                        {isPaused ? 'Resume' : 'Pause'}
                    </button>
                    <button 
                        onClick={stopScan} 
                        className="flex-1 py-2 bg-red-600 hover:bg-red-500 rounded font-bold text-white transition-colors"
                    >
                        Stop
                    </button>
                </div>
            )}
        </div>
      </div>

      {/* Progress & Logs */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden flex flex-col flex-1 min-h-0">
          <div className="p-4 border-b border-gray-700 bg-gray-800">
              <div className="flex justify-between text-xs font-bold uppercase text-gray-400 mb-2">
                  <span>{isScanning ? (isPaused ? 'Paused' : `Scanning: ${currentFile}`) : 'Ready / Complete'}</span>
                  <span>{progress}%</span>
              </div>
              <div className="h-2 bg-gray-900 rounded-full overflow-hidden">
                  <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
                      style={{ width: `${progress}%` }}
                  ></div>
              </div>
          </div>

          <div className="flex flex-1 min-h-0 bg-black/20">
              <div className="w-full flex flex-col">
                  <div className="px-4 py-2 bg-gray-900 border-b border-gray-700 text-xs font-bold text-gray-500 uppercase">System Log</div>
                  <div ref={logContainerRef} className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1.5 scroll-smooth">
                      {scanLog.length === 0 && <div className="text-gray-600 italic">Waiting for activity...</div>}
                      {scanLog.map((log, i) => {
                           let color = 'text-gray-400';
                           if (log.includes('[ERROR]')) color = 'text-red-400';
                           else if (log.includes('[SUCCESS]')) color = 'text-green-400';
                           else if (log.includes('[SYSTEM]')) color = 'text-blue-400';
                           return <div key={i} className={`${color} break-all border-b border-gray-800/50 pb-0.5`}>{log}</div>
                      })}
                  </div>
              </div>
          </div>
      </div>
    </div>
  );
};
