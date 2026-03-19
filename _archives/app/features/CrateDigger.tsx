
import React, { useState } from 'react';
import { mockFileDatabase, MockTrack } from '../mockData';
import { Icons } from '../Icons';

export const CrateDigger = () => {
    const [selectedTrackId, setSelectedTrackId] = useState<string>('');
    const [recommendations, setRecommendations] = useState<(MockTrack & { score: number, reason: string })[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    const handleTrackSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSelectedTrackId(e.target.value);
        setRecommendations([]);
    };

    const findSimilarTracks = async () => {
        if (!selectedTrackId) return;
        
        setIsSearching(true);
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1200));

        const sourceTrack = mockFileDatabase.find(t => t.id === selectedTrackId);
        if (!sourceTrack) {
            setIsSearching(false);
            return;
        }

        // Logic for finding similarities
        const results = mockFileDatabase
            .filter(t => t.id !== sourceTrack.id) // Exclude self
            .map(track => {
                let score = 0;
                let reasons = [];

                // BPM Score (within 5 BPM is good)
                const bpmDiff = Math.abs(track.bpm - sourceTrack.bpm);
                if (bpmDiff <= 2) { score += 40; reasons.push('Perfect BPM Match'); }
                else if (bpmDiff <= 5) { score += 20; reasons.push('Similar BPM'); }

                // Genre Score
                if (track.genre === sourceTrack.genre) { score += 30; reasons.push('Same Genre'); }

                // Key Score (Mocking simple match)
                if (track.key === sourceTrack.key) { score += 30; reasons.push('Harmonic Match'); }

                return { ...track, score, reason: reasons.join(', ') };
            })
            .filter(t => t.score >= 30) // Only show relevant results
            .sort((a, b) => b.score - a.score);

        setRecommendations(results);
        setIsSearching(false);
    };

    const sourceTrack = mockFileDatabase.find(t => t.id === selectedTrackId);

    return (
        <div className="space-y-6">
            {/* Search Panel */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 className="text-lg font-medium text-gray-200 mb-4 flex items-center gap-2">
                    <Icons.Search /> Find Similar Tracks (Crate Digging)
                </h3>
                <div className="flex gap-4">
                    <div className="flex-1">
                        <label className="block text-sm text-gray-400 mb-1">Select Source Track</label>
                        <select 
                            value={selectedTrackId} 
                            onChange={handleTrackSelect}
                            className="w-full bg-gray-900 border border-gray-600 rounded px-4 py-2 text-gray-100 focus:border-blue-500"
                        >
                            <option value="">-- Choose a track from library --</option>
                            {mockFileDatabase.map(t => (
                                <option key={t.id} value={t.id}>{t.artist} - {t.title} ({t.bpm} BPM, {t.key})</option>
                            ))}
                        </select>
                    </div>
                    <div className="flex items-end">
                        <button 
                            onClick={findSimilarTracks} 
                            disabled={!selectedTrackId || isSearching}
                            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded font-bold transition-colors h-[42px]"
                        >
                            {isSearching ? 'Digging...' : 'Find Matches'}
                        </button>
                    </div>
                </div>

                {/* Source Track Details Preview */}
                {sourceTrack && (
                    <div className="mt-4 p-3 bg-gray-900/50 rounded border border-gray-700 flex gap-6 text-sm text-gray-400">
                        <div><span className="font-bold text-gray-300">Genre:</span> {sourceTrack.genre}</div>
                        <div><span className="font-bold text-gray-300">BPM:</span> {sourceTrack.bpm}</div>
                        <div><span className="font-bold text-gray-300">Key:</span> {sourceTrack.key}</div>
                    </div>
                )}
            </div>

            {/* Results Grid */}
            {recommendations.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {recommendations.map((track) => (
                        <div key={track.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700 hover:border-blue-500 transition-colors group">
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <div className="font-bold text-gray-100">{track.title}</div>
                                    <div className="text-sm text-gray-400">{track.artist}</div>
                                </div>
                                <div className={`text-xl font-bold ${track.score > 80 ? 'text-green-400' : 'text-blue-400'}`}>
                                    {track.score}%
                                </div>
                            </div>
                            
                            <div className="flex gap-2 text-xs text-gray-500 font-mono mb-3">
                                <span className="bg-gray-900 px-2 py-1 rounded">{track.bpm} BPM</span>
                                <span className="bg-gray-900 px-2 py-1 rounded">{track.key}</span>
                                <span className="bg-gray-900 px-2 py-1 rounded">{track.genre}</span>
                            </div>

                            <div className="text-xs text-blue-300 flex gap-1 items-center">
                                <Icons.Sparkles /> Match: {track.reason}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {!isSearching && selectedTrackId && recommendations.length === 0 && (
                <div className="text-center text-gray-500 py-10">
                    No similar tracks found based on BPM, Key, and Genre criteria.
                </div>
            )}
        </div>
    );
};
