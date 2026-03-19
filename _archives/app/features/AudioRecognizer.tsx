
import React, { useState } from 'react';
import { mockExternalDBResults, MockRecognitionResult } from '../mockData';

export const AudioRecognizer = () => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [recognitionMethod, setRecognitionMethod] = useState<'fingerprint' | 'metadata'>('fingerprint');
    const [trackInfoInput, setTrackInfoInput] = useState('');
    const [results, setResults] = useState<MockRecognitionResult[]>([]);
    const [isRecognizing, setIsRecognizing] = useState(false);

    const handleRecognize = async () => {
        setIsRecognizing(true);
        setResults([]);
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        setResults(mockExternalDBResults);
        setIsRecognizing(false);
    };

    return (
        <div className="space-y-6">
             <div className="flex gap-4 mb-4">
                <label className="flex items-center gap-2 cursor-pointer bg-gray-800 px-4 py-2 rounded">
                    <input type="radio" checked={recognitionMethod === 'fingerprint'} onChange={() => setRecognitionMethod('fingerprint')} />
                    <span>Audio Fingerprint</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer bg-gray-800 px-4 py-2 rounded">
                    <input type="radio" checked={recognitionMethod === 'metadata'} onChange={() => setRecognitionMethod('metadata')} />
                    <span>Metadata Search</span>
                </label>
             </div>

             {recognitionMethod === 'fingerprint' ? (
                <div className="bg-gray-800 p-4 rounded border border-gray-700">
                    <input type="file" onChange={e => setSelectedFile(e.target.files?.[0] || null)} className="text-gray-300" />
                </div>
             ) : (
                <input type="text" value={trackInfoInput} onChange={e => setTrackInfoInput(e.target.value)} placeholder="Artist - Title" className="w-full bg-gray-800 p-3 rounded text-gray-100 border border-gray-700" />
             )}

             <button onClick={handleRecognize} disabled={isRecognizing} className="px-6 py-2 bg-blue-600 rounded font-bold w-full">
                {isRecognizing ? 'Recognizing...' : 'Identify Track'}
             </button>

             {results.length > 0 && (
                 <div className="space-y-4">
                     {results.map(res => (
                         <div key={res.id} className="bg-gray-800 p-4 rounded flex gap-4 items-center">
                             <div className="w-16 h-16 bg-gray-700 rounded overflow-hidden">
                                {res.artworkUrl && <img src={res.artworkUrl} alt="Art" />}
                             </div>
                             <div className="flex-1">
                                 <div className="font-bold text-white">{res.title}</div>
                                 <div className="text-gray-400">{res.artist}</div>
                                 <div className="text-xs text-gray-500">{res.album} ({res.year})</div>
                             </div>
                             <div className="text-right">
                                 <div className="text-green-400 font-bold">{Math.round(res.confidence * 100)}%</div>
                                 <div className="text-xs text-gray-500">{res.source}</div>
                             </div>
                         </div>
                     ))}
                 </div>
             )}
        </div>
    );
};
