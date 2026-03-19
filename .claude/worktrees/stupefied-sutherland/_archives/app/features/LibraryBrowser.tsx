
import React, { useState, useEffect, useMemo } from 'react';
import { db, Track } from '../db';
import { Icons } from '../Icons';

export const LibraryBrowser = () => {
    const [tracks, setTracks] = useState<Track[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedTrackId, setSelectedTrackId] = useState<number | null>(null);
    const [sortConfig, setSortConfig] = useState<{ key: keyof Track; direction: 'asc' | 'desc' }>({ key: 'dateAdded', direction: 'desc' });
    const [isInspectorOpen, setIsInspectorOpen] = useState(true);
    const [editForm, setEditForm] = useState<Partial<Track>>({});
    const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

    // Load data from Real DB
    useEffect(() => {
        const loadTracks = async () => {
            const allTracks = await db.tracks.toArray();
            setTracks(allTracks);
        };
        loadTracks();
    }, []);

    // Filter & Sort Logic
    const processedTracks = useMemo(() => {
        let result = [...tracks];

        // 1. Filter
        if (searchQuery) {
            const q = searchQuery.toLowerCase();
            result = result.filter(t => 
                t.title.toLowerCase().includes(q) || 
                t.artist.toLowerCase().includes(q) ||
                t.album.toLowerCase().includes(q) ||
                t.genre.toLowerCase().includes(q)
            );
        }

        // 2. Sort
        result.sort((a, b) => {
            const aVal = a[sortConfig.key] || '';
            const bVal = b[sortConfig.key] || '';
            
            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });

        return result;
    }, [tracks, searchQuery, sortConfig]);

    const handleSort = (key: keyof Track) => {
        setSortConfig(current => ({
            key,
            direction: current.key === key && current.direction === 'asc' ? 'desc' : 'asc'
        }));
    };

    const handleSelect = (track: Track) => {
        setSelectedTrackId(track.id!);
        setEditForm(track);
    };

    const handleSave = async () => {
        if (selectedTrackId && editForm) {
            await db.tracks.update(selectedTrackId, editForm);
            // Refresh local state
            setTracks(prev => prev.map(t => t.id === selectedTrackId ? { ...t, ...editForm } : t));
            alert('Changes saved to Database!');
        }
    };

    const handleDelete = async () => {
        if (selectedTrackId && confirm('Are you sure you want to delete this track from the library?')) {
            await db.tracks.delete(selectedTrackId);
            setTracks(prev => prev.filter(t => t.id !== selectedTrackId));
            setSelectedTrackId(null);
        }
    };

    const formatTime = (seconds: number) => {
        if (!seconds) return '--:--';
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className="flex flex-col h-full gap-4">
            {/* Toolbar */}
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 flex flex-wrap gap-4 justify-between items-center shadow-sm">
                <div className="flex items-center gap-4 flex-1">
                    <div className="relative flex-1 max-w-md">
                        <Icons.Search className="absolute left-3 top-2.5 text-gray-500 w-5 h-5" />
                        <input 
                            type="text" 
                            placeholder="Search library..." 
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            className="w-full bg-gray-900 border border-gray-600 rounded-full pl-10 pr-4 py-2 text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                        />
                    </div>
                    <div className="text-sm text-gray-400 font-mono">
                        {processedTracks.length} tracks
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <button 
                        onClick={() => setViewMode('list')}
                        className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Icons.ListMusic width={20} />
                    </button>
                    <button 
                        onClick={() => setViewMode('grid')}
                        className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Icons.Square width={20} />
                    </button>
                    <div className="w-px h-6 bg-gray-700 mx-2"></div>
                    <button 
                        onClick={() => setIsInspectorOpen(!isInspectorOpen)}
                        className={`p-2 rounded transition-colors ${isInspectorOpen ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:text-white'}`}
                        title="Toggle Inspector"
                    >
                        <Icons.Palette width={20} />
                    </button>
                </div>
            </div>

            {/* Main Workspace */}
            <div className="flex flex-1 min-h-0 gap-4">
                
                {/* Track List */}
                <div className="flex-1 bg-gray-800 rounded-lg border border-gray-700 overflow-hidden flex flex-col shadow-sm">
                    {/* Table Header */}
                    <div className="flex bg-gray-900 border-b border-gray-700 text-xs font-bold text-gray-400 uppercase tracking-wider sticky top-0 z-10">
                        <div onClick={() => handleSort('title')} className="flex-1 px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors flex items-center gap-1">
                            Title {sortConfig.key === 'title' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </div>
                        <div onClick={() => handleSort('artist')} className="w-1/4 px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors hidden md:block">
                            Artist {sortConfig.key === 'artist' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                        </div>
                        <div onClick={() => handleSort('bpm')} className="w-20 px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors text-right">
                            BPM
                        </div>
                        <div onClick={() => handleSort('key')} className="w-20 px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors text-center hidden sm:block">
                            Key
                        </div>
                        <div onClick={() => handleSort('duration')} className="w-20 px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors text-right">
                            Time
                        </div>
                    </div>

                    {/* Scrollable Content */}
                    <div className="flex-1 overflow-y-auto">
                        {processedTracks.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                <Icons.Music className="w-16 h-16 mb-4 opacity-20" />
                                <p>No tracks found.</p>
                                <p className="text-xs">Import some files using the Scanner.</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-gray-700/50">
                                {processedTracks.map(track => (
                                    <div 
                                        key={track.id}
                                        onClick={() => handleSelect(track)}
                                        onDoubleClick={() => alert(`Playing: ${track.title}`)} // Hook to player later
                                        className={`flex items-center text-sm cursor-pointer transition-colors hover:bg-gray-700/40 ${selectedTrackId === track.id ? 'bg-blue-900/20 border-l-2 border-blue-500' : 'border-l-2 border-transparent'}`}
                                    >
                                        <div className="flex-1 px-4 py-3 font-medium text-gray-200 truncate">
                                            {track.title}
                                            <div className="md:hidden text-xs text-gray-500">{track.artist}</div>
                                        </div>
                                        <div className="w-1/4 px-4 py-3 text-gray-400 truncate hidden md:block">
                                            {track.artist}
                                        </div>
                                        <div className="w-20 px-4 py-3 text-right font-mono text-blue-300">
                                            {track.bpm || '-'}
                                        </div>
                                        <div className="w-20 px-4 py-3 text-center font-mono text-gray-400 hidden sm:block">
                                            {track.key || '-'}
                                        </div>
                                        <div className="w-20 px-4 py-3 text-right text-gray-500 font-mono">
                                            {formatTime(track.duration)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Inspector Panel */}
                {isInspectorOpen && (
                    <div className="w-80 bg-gray-800 rounded-lg border border-gray-700 flex flex-col shadow-xl animate-in slide-in-from-right duration-200">
                        <div className="p-4 border-b border-gray-700 font-bold text-gray-200 flex justify-between items-center bg-gray-900/50">
                            <span>Track Inspector</span>
                            <button onClick={() => setIsInspectorOpen(false)} className="text-gray-500 hover:text-white">
                                <Icons.ArrowRight className="w-4 h-4" />
                            </button>
                        </div>
                        
                        {selectedTrackId ? (
                            <div className="p-6 flex-1 overflow-y-auto space-y-6">
                                {/* Cover Placeholder */}
                                <div className="w-full aspect-square bg-gray-900 rounded-lg border border-gray-700 flex items-center justify-center text-gray-600 shadow-inner">
                                    <Icons.Music className="w-20 h-20 opacity-50" />
                                </div>

                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Title</label>
                                        <input 
                                            type="text" 
                                            value={editForm.title || ''} 
                                            onChange={e => setEditForm({...editForm, title: e.target.value})}
                                            className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100 focus:border-blue-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Artist</label>
                                        <input 
                                            type="text" 
                                            value={editForm.artist || ''} 
                                            onChange={e => setEditForm({...editForm, artist: e.target.value})}
                                            className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100 focus:border-blue-500"
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">BPM</label>
                                            <input 
                                                type="number" 
                                                value={editForm.bpm || ''} 
                                                onChange={e => setEditForm({...editForm, bpm: Number(e.target.value)})}
                                                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100 focus:border-blue-500 font-mono text-center"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Key</label>
                                            <input 
                                                type="text" 
                                                value={editForm.key || ''} 
                                                onChange={e => setEditForm({...editForm, key: e.target.value})}
                                                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100 focus:border-blue-500 font-mono text-center"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Genre</label>
                                        <input 
                                            type="text" 
                                            value={editForm.genre || ''} 
                                            onChange={e => setEditForm({...editForm, genre: e.target.value})}
                                            className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-100 focus:border-blue-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-gray-500 uppercase mb-1">File Path</label>
                                        <div className="text-xs text-gray-500 break-all font-mono bg-gray-900 p-2 rounded">
                                            {editForm.path}
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-gray-700 flex flex-col gap-3">
                                    <button onClick={handleSave} className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded font-bold shadow-lg transition-colors">
                                        Save Changes
                                    </button>
                                    <div className="flex gap-2">
                                        <button className="flex-1 py-2 bg-purple-600/20 hover:bg-purple-600/40 text-purple-400 border border-purple-500/50 rounded font-medium text-xs transition-colors">
                                            Analyze AI
                                        </button>
                                        <button onClick={handleDelete} className="flex-1 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 border border-red-500/50 rounded font-medium text-xs transition-colors">
                                            Delete Track
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 p-6 text-center">
                                <Icons.ListMusic className="w-12 h-12 mb-3 opacity-30" />
                                <p>Select a track to view details and edit metadata.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
