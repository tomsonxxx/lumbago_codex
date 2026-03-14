
import React, { useState, useEffect } from 'react';
import { mockFileDatabase, MockTrack } from '../mockData';
import { Icons } from '../Icons';

type Operator = 'equals' | 'contains' | 'gt' | 'lt';
type Field = 'genre' | 'bpm' | 'year' | 'artist' | 'key';

interface Rule {
    id: string;
    field: Field;
    operator: Operator;
    value: string;
}

interface Collection {
    id: string;
    name: string;
    rules: Rule[];
    matchType: 'all' | 'any';
}

export const SmartCollections = () => {
    const [collections, setCollections] = useState<Collection[]>([
        { 
            id: 'c1', 
            name: 'High Energy Techno', 
            matchType: 'all',
            rules: [
                { id: 'r1', field: 'genre', operator: 'contains', value: 'Techno' },
                { id: 'r2', field: 'bpm', operator: 'gt', value: '128' }
            ] 
        }
    ]);
    const [selectedCollectionId, setSelectedCollectionId] = useState<string>('c1');
    const [editingCollection, setEditingCollection] = useState<Collection | null>(null);
    const [results, setResults] = useState<MockTrack[]>([]);

    // Filter Logic
    useEffect(() => {
        const activeCollection = editingCollection || collections.find(c => c.id === selectedCollectionId);
        if (!activeCollection) {
            setResults([]);
            return;
        }

        const filtered = mockFileDatabase.filter(track => {
            const matches = activeCollection.rules.map(rule => {
                const trackValue = String(track[rule.field]).toLowerCase();
                const ruleValue = rule.value.toLowerCase();

                switch (rule.operator) {
                    case 'contains': return trackValue.includes(ruleValue);
                    case 'equals': return trackValue === ruleValue;
                    case 'gt': return parseFloat(trackValue) > parseFloat(ruleValue);
                    case 'lt': return parseFloat(trackValue) < parseFloat(ruleValue);
                    default: return false;
                }
            });

            if (activeCollection.matchType === 'all') {
                return matches.every(m => m);
            } else {
                return matches.some(m => m);
            }
        });

        setResults(filtered);
    }, [selectedCollectionId, collections, editingCollection]);

    const handleCreate = () => {
        const newCol: Collection = {
            id: `c${Date.now()}`,
            name: 'New Smart Collection',
            matchType: 'all',
            rules: [{ id: `r${Date.now()}`, field: 'genre', operator: 'contains', value: '' }]
        };
        setEditingCollection(newCol);
    };

    const handleSave = () => {
        if (!editingCollection) return;
        
        if (collections.find(c => c.id === editingCollection.id)) {
            setCollections(prev => prev.map(c => c.id === editingCollection.id ? editingCollection : c));
        } else {
            setCollections(prev => [...prev, editingCollection]);
            setSelectedCollectionId(editingCollection.id);
        }
        setEditingCollection(null);
    };

    const addRule = () => {
        if (!editingCollection) return;
        setEditingCollection({
            ...editingCollection,
            rules: [...editingCollection.rules, { id: `r${Date.now()}`, field: 'genre', operator: 'contains', value: '' }]
        });
    };

    const removeRule = (ruleId: string) => {
        if (!editingCollection) return;
        setEditingCollection({
            ...editingCollection,
            rules: editingCollection.rules.filter(r => r.id !== ruleId)
        });
    };

    const updateRule = (ruleId: string, updates: Partial<Rule>) => {
        if (!editingCollection) return;
        setEditingCollection({
            ...editingCollection,
            rules: editingCollection.rules.map(r => r.id === ruleId ? { ...r, ...updates } : r)
        });
    };

    const renderEditor = () => {
        if (!editingCollection) return null;
        return (
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-6">
                <div className="flex justify-between mb-4">
                    <input 
                        value={editingCollection.name}
                        onChange={e => setEditingCollection({...editingCollection, name: e.target.value})}
                        className="bg-transparent text-xl font-bold border-b border-gray-600 focus:border-blue-500 outline-none pb-1 w-full mr-4"
                        placeholder="Collection Name"
                    />
                    <div className="flex gap-2">
                        <button onClick={() => setEditingCollection(null)} className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">Cancel</button>
                        <button onClick={handleSave} className="px-4 py-2 bg-green-600 rounded hover:bg-green-500 font-bold">Save Collection</button>
                    </div>
                </div>

                <div className="flex items-center gap-2 mb-4 text-sm text-gray-400">
                    <span>Match</span>
                    <select 
                        value={editingCollection.matchType}
                        onChange={e => setEditingCollection({...editingCollection, matchType: e.target.value as any})}
                        className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-white"
                    >
                        <option value="all">ALL</option>
                        <option value="any">ANY</option>
                    </select>
                    <span>of the following rules:</span>
                </div>

                <div className="space-y-3">
                    {editingCollection.rules.map(rule => (
                        <div key={rule.id} className="flex gap-2 items-center bg-gray-900/50 p-2 rounded">
                            <select 
                                value={rule.field}
                                onChange={e => updateRule(rule.id, { field: e.target.value as Field })}
                                className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm w-32"
                            >
                                <option value="genre">Genre</option>
                                <option value="bpm">BPM</option>
                                <option value="year">Year</option>
                                <option value="artist">Artist</option>
                                <option value="key">Key</option>
                            </select>

                            <select 
                                value={rule.operator}
                                onChange={e => updateRule(rule.id, { operator: e.target.value as Operator })}
                                className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm w-32"
                            >
                                <option value="contains">contains</option>
                                <option value="equals">is</option>
                                <option value="gt">greater than</option>
                                <option value="lt">less than</option>
                            </select>

                            <input 
                                type="text"
                                value={rule.value}
                                onChange={e => updateRule(rule.id, { value: e.target.value })}
                                className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm flex-1"
                                placeholder="Value..."
                            />

                            <button onClick={() => removeRule(rule.id)} className="text-red-400 hover:text-red-300 px-2">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                            </button>
                        </div>
                    ))}
                </div>
                
                <button onClick={addRule} className="mt-4 text-blue-400 text-sm hover:underline flex items-center gap-1">
                    + Add Rule
                </button>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex gap-4 overflow-x-auto pb-2">
                    {collections.map(col => (
                        <button
                            key={col.id}
                            onClick={() => { setSelectedCollectionId(col.id); setEditingCollection(null); }}
                            className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors border ${selectedCollectionId === col.id && !editingCollection ? 'bg-blue-600 border-blue-500 text-white' : 'bg-gray-800 border-gray-700 text-gray-400 hover:bg-gray-700'}`}
                        >
                            {col.name}
                        </button>
                    ))}
                    <button onClick={handleCreate} className="px-4 py-2 bg-gray-800 border border-dashed border-gray-600 text-gray-400 hover:text-white rounded-lg hover:border-gray-400 transition-colors">
                        + New Collection
                    </button>
                </div>
                {selectedCollectionId && !editingCollection && (
                    <button 
                        onClick={() => setEditingCollection(collections.find(c => c.id === selectedCollectionId) || null)}
                        className="text-gray-400 hover:text-white px-3"
                    >
                        Edit Rules
                    </button>
                )}
            </div>

            {renderEditor()}

            {!editingCollection && (
                <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-700 flex justify-between items-center bg-gray-900/30">
                        <span className="font-bold text-gray-300">
                            {collections.find(c => c.id === selectedCollectionId)?.name} Results
                        </span>
                        <span className="bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded-full">
                            {results.length} Tracks
                        </span>
                    </div>
                    {results.length > 0 ? (
                        <table className="w-full text-left text-sm">
                            <thead className="bg-gray-900 text-gray-500 uppercase font-medium text-xs">
                                <tr>
                                    <th className="px-6 py-3">Artist</th>
                                    <th className="px-6 py-3">Title</th>
                                    <th className="px-6 py-3">Genre</th>
                                    <th className="px-6 py-3 text-right">BPM</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700">
                                {results.map(track => (
                                    <tr key={track.id} className="hover:bg-gray-700/50 transition-colors">
                                        <td className="px-6 py-3 font-medium text-gray-300">{track.artist}</td>
                                        <td className="px-6 py-3 text-gray-400">{track.title}</td>
                                        <td className="px-6 py-3 text-gray-400">
                                            <span className="bg-gray-700 px-2 py-0.5 rounded text-xs">{track.genre}</span>
                                        </td>
                                        <td className="px-6 py-3 text-right font-mono text-blue-400">{track.bpm}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <div className="p-12 text-center text-gray-500">
                            No tracks match the current rules.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
