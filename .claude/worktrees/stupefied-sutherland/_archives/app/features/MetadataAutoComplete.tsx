
import React, { useState } from 'react';
import { mockFileDatabase, MockTrack } from '../mockData';
import { Icons } from '../Icons';

interface IncompleteTrack extends MockTrack {
    missingFields: string[];
    suggestion?: Partial<MockTrack> & { source: string };
}

export const MetadataAutoComplete = () => {
    const [scanStatus, setScanStatus] = useState<'idle' | 'scanning' | 'complete'>('idle');
    const [incompleteTracks, setIncompleteTracks] = useState<IncompleteTrack[]>([]);
    const [isFetching, setIsFetching] = useState(false);
    
    // Simulate finding tracks with missing data
    const scanLibrary = async () => {
        setScanStatus('scanning');
        setIncompleteTracks([]);
        
        await new Promise(r => setTimeout(r, 1500));
        
        // Mock finding incomplete tracks
        const found: IncompleteTrack[] = mockFileDatabase.slice(0, 3).map(t => ({
            ...t,
            missingFields: ['year', 'label', 'key'],
            suggestion: undefined
        }));
        
        // Add a severely incomplete mock track
        found.push({
            id: 'inc_1',
            path: '/Downloads/unknown_track_01.mp3',
            title: 'Track 01',
            artist: 'Unknown Artist',
            album: '',
            genre: '',
            year: '',
            bpm: 0,
            key: '',
            duration: 0,
            fileSize: 0,
            fingerprint: '',
            hash: '',
            missingFields: ['artist', 'album', 'genre', 'year', 'bpm', 'key']
        });

        setIncompleteTracks(found);
        setScanStatus('complete');
    };

    const fetchMetadata = async () => {
        setIsFetching(true);
        
        // Simulate API calls to MusicBrainz/Discogs
        const updated = await Promise.all(incompleteTracks.map(async (track) => {
            await new Promise(r => setTimeout(r, Math.random() * 500 + 200));
            return {
                ...track,
                suggestion: {
                    artist: track.artist === 'Unknown Artist' ? 'The Weeknd' : track.artist,
                    title: track.title === 'Track 01' ? 'Blinding Lights' : track.title,
                    album: 'After Hours',
                    year: '2020',
                    genre: 'Synthpop',
                    bpm: 171,
                    key: 'Fm',
                    source: 'MusicBrainz'
                }
            };
        }));

        setIncompleteTracks(updated);
        setIsFetching(false);
    };

    const applyUpdate = (id: string) => {
        setIncompleteTracks(prev => prev.filter(t => t.id !== id));
        // In a real app, this would update the main database
    };

    const applyAll = () => {
        setIncompleteTracks([]);
    };

    return (
        <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mb-4 text-purple-400">
                    <Icons.Tags width={32} height={32} />
                </div>
                <h3 className="text-xl font-bold text-gray-200 mb-2">Metadata Auto-Complete</h3>
                <p className="text-gray-400 max-w-lg mb-6">
                    Scan your library for missing tags (Artwork, Year, Key, etc.) and automatically fetch them from MusicBrainz and Discogs.
                </p>
                
                {scanStatus === 'idle' && (
                    <button onClick={scanLibrary} className="px-8 py-3 bg-blue-600 hover:bg-blue-500 rounded-full font-bold shadow-lg shadow-blue-900/50 transition-transform active:scale-95">
                        Start Library Scan
                    </button>
                )}
                
                {scanStatus === 'scanning' && (
                    <div className="w-full max-w-md space-y-2">
                        <div className="flex justify-between text-xs text-gray-400 uppercase">
                            <span>Scanning Library...</span>
                            <span>45%</span>
                        </div>
                        <div className="h-2 bg-gray-900 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 w-[45%] animate-pulse"></div>
                        </div>
                    </div>
                )}
            </div>

            {scanStatus === 'complete' && (
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <h4 className="text-lg font-medium text-gray-300">
                            Found {incompleteTracks.length} tracks with missing metadata
                        </h4>
                        <div className="flex gap-2">
                            <button 
                                onClick={fetchMetadata} 
                                disabled={isFetching || incompleteTracks.every(t => t.suggestion)}
                                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded font-medium disabled:opacity-50"
                            >
                                {isFetching ? 'Fetching Data...' : 'Fetch Metadata'}
                            </button>
                            <button 
                                onClick={applyAll}
                                disabled={!incompleteTracks.some(t => t.suggestion)}
                                className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded font-medium disabled:opacity-50"
                            >
                                Apply All
                            </button>
                        </div>
                    </div>

                    <div className="grid gap-4">
                        {incompleteTracks.map(track => (
                            <div key={track.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700 flex flex-col md:flex-row gap-4">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-bold text-gray-200">{track.title}</span>
                                        <span className="text-gray-500">-</span>
                                        <span className="text-gray-400">{track.artist}</span>
                                    </div>
                                    <div className="text-xs text-gray-500 font-mono mb-2">{track.path}</div>
                                    <div className="flex flex-wrap gap-2">
                                        {track.missingFields.map(field => (
                                            <span key={field} className="text-xs bg-red-900/30 text-red-400 px-2 py-0.5 rounded border border-red-900/50">
                                                Missing: {field}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="hidden md:block w-px bg-gray-700"></div>

                                <div className="flex-1 md:max-w-md">
                                    {track.suggestion ? (
                                        <div className="h-full flex flex-col justify-between">
                                            <div className="text-sm">
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="text-xs font-bold text-green-400 uppercase tracking-wider">Suggestion Found</span>
                                                    <span className="text-xs text-gray-500">{track.suggestion.source}</span>
                                                </div>
                                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-gray-300">
                                                    <div><span className="text-gray-500">Artist:</span> {track.suggestion.artist}</div>
                                                    <div><span className="text-gray-500">Year:</span> {track.suggestion.year}</div>
                                                    <div><span className="text-gray-500">Album:</span> {track.suggestion.album}</div>
                                                    <div><span className="text-gray-500">Key:</span> {track.suggestion.key}</div>
                                                </div>
                                            </div>
                                            <button 
                                                onClick={() => applyUpdate(track.id)}
                                                className="mt-3 w-full py-1.5 bg-gray-700 hover:bg-green-600/20 hover:text-green-400 border border-gray-600 hover:border-green-500 rounded text-sm transition-colors"
                                            >
                                                Apply Update
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="h-full flex items-center justify-center text-gray-600 italic text-sm border-2 border-dashed border-gray-700 rounded">
                                            Waiting for fetch...
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
