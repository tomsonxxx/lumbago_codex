
import React, { useState, useEffect } from 'react';
import { mockFileDatabase, MockTrack } from '../mockData';
import { Icons } from '../Icons';

// Helper to map standard keys to Camelot notation for simulation
const getCamelotKey = (key: string): string => {
    const map: Record<string, string> = {
        'Am': '8A', 'C': '8B', 
        'Em': '9A', 'G': '9B', 
        'Bm': '10A', 'D': '10B',
        'F#m': '11A', 'A': '11B',
        'C#m': '12A', 'E': '12B',
        'G#m': '1A', 'B': '1B',
        'D#m': '2A', 'F#': '2B',
        'A#m': '3A', 'C#': '3B',
        'Fm': '4A', 'G#': '4B',
        'Cm': '5A', 'D#': '5B',
        'Gm': '6A', 'A#': '6B',
        'Dm': '7A', 'F': '7B'
    };
    return map[key] || 'Unknown';
};

// Simulate energy level based on BPM and Genre
const getEnergyLevel = (track: MockTrack): number => {
    let base = track.bpm / 1.8; // e.g. 128 bpm -> ~70
    if (track.genre === 'Deep House') base -= 10;
    if (track.genre === 'Techno') base += 10;
    if (track.genre === 'Chillout') base -= 30;
    return Math.min(100, Math.max(10, Math.round(base)));
};

export const PlaylistIntelligence = () => {
    const [playlist, setPlaylist] = useState<(MockTrack & { camelot: string, energy: number })[]>([]);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [mode, setMode] = useState<'harmonic' | 'energy' | 'bpm'>('harmonic');

    // Load random initial playlist
    useEffect(() => {
        const initial = mockFileDatabase.slice(0, 8).map(t => ({
            ...t,
            camelot: getCamelotKey(t.key),
            energy: getEnergyLevel(t)
        }));
        setPlaylist(initial);
    }, []);

    const optimizePlaylist = async () => {
        setIsOptimizing(true);
        await new Promise(resolve => setTimeout(resolve, 800));

        let sorted = [...playlist];

        if (mode === 'harmonic') {
            // Simple harmonic sort simulation (group by key proximity)
            sorted.sort((a, b) => a.camelot.localeCompare(b.camelot));
        } else if (mode === 'energy') {
            // Ramp up energy
            sorted.sort((a, b) => a.energy - b.energy);
        } else if (mode === 'bpm') {
            sorted.sort((a, b) => a.bpm - b.bpm);
        }

        setPlaylist(sorted);
        setIsOptimizing(false);
    };

    const shufflePlaylist = () => {
        const shuffled = [...playlist].sort(() => Math.random() - 0.5);
        setPlaylist(shuffled);
    };

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 flex flex-wrap gap-4 items-center justify-between">
                <div className="flex gap-2">
                    <button 
                        onClick={() => setMode('harmonic')}
                        className={`px-4 py-2 rounded font-medium text-sm transition-colors ${mode === 'harmonic' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                    >
                        Harmonic Mixing
                    </button>
                    <button 
                        onClick={() => setMode('energy')}
                        className={`px-4 py-2 rounded font-medium text-sm transition-colors ${mode === 'energy' ? 'bg-yellow-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                    >
                        Energy Flow
                    </button>
                    <button 
                        onClick={() => setMode('bpm')}
                        className={`px-4 py-2 rounded font-medium text-sm transition-colors ${mode === 'bpm' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'}`}
                    >
                        BPM Match
                    </button>
                </div>
                <div className="flex gap-2">
                    <button onClick={shufflePlaylist} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium">
                        Shuffle
                    </button>
                    <button 
                        onClick={optimizePlaylist} 
                        disabled={isOptimizing}
                        className="px-6 py-2 bg-green-600 hover:bg-green-500 rounded text-sm font-bold flex items-center gap-2"
                    >
                        <Icons.Sparkles /> {isOptimizing ? 'Optimizing...' : 'Optimize Order'}
                    </button>
                </div>
            </div>

            {/* Visualizer */}
            <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg h-48 flex items-end justify-between gap-1 relative">
                <div className="absolute top-2 left-2 text-xs text-gray-500 font-mono">ENERGY / FLOW VIZ</div>
                {playlist.map((track, idx) => (
                    <div key={track.id} className="flex-1 flex flex-col items-center gap-2 group relative">
                        <div 
                            className={`w-full rounded-t transition-all duration-500 ${mode === 'harmonic' ? 'bg-purple-500/50' : mode === 'energy' ? 'bg-yellow-500/50' : 'bg-blue-500/50'}`}
                            style={{ height: `${track.energy}%` }}
                        >
                            <div className="opacity-0 group-hover:opacity-100 absolute bottom-full mb-2 bg-black text-xs p-1 rounded whitespace-nowrap z-10">
                                {track.bpm} BPM / {track.camelot}
                            </div>
                        </div>
                    </div>
                ))}
                {/* Connection Lines (Simulated with border) */}
                <div className="absolute bottom-0 w-full h-1 bg-gray-800"></div>
            </div>

            {/* Playlist Table */}
            <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-900 text-gray-400 uppercase font-medium text-xs">
                        <tr>
                            <th className="px-4 py-3">#</th>
                            <th className="px-4 py-3">Title</th>
                            <th className="px-4 py-3">Artist</th>
                            <th className="px-4 py-3 text-center">BPM</th>
                            <th className="px-4 py-3 text-center">Key (Camelot)</th>
                            <th className="px-4 py-3 text-center">Energy</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {playlist.map((track, idx) => (
                            <tr key={track.id} className="hover:bg-gray-700/50 transition-colors">
                                <td className="px-4 py-3 text-gray-500 font-mono">{idx + 1}</td>
                                <td className="px-4 py-3 font-medium text-gray-200">{track.title}</td>
                                <td className="px-4 py-3 text-gray-400">{track.artist}</td>
                                <td className="px-4 py-3 text-center font-mono text-blue-300">{track.bpm}</td>
                                <td className="px-4 py-3 text-center font-mono">
                                    <span className={`px-2 py-1 rounded text-xs ${mode === 'harmonic' ? 'bg-purple-900 text-purple-300 border border-purple-700' : 'bg-gray-700'}`}>
                                        {track.camelot}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-center">
                                    <div className="w-full bg-gray-900 rounded-full h-1.5">
                                        <div className="bg-yellow-500 h-1.5 rounded-full" style={{ width: `${track.energy}%` }}></div>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
