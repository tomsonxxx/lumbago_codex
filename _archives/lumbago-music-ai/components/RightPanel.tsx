
import React, { useMemo } from 'react';
import { AudioFile } from '../types';
import AlbumCover from './AlbumCover';
import { findMixSuggestions } from '../utils/djUtils';
// @ts-ignore
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
// @ts-ignore
import _ from 'lodash';

interface RightPanelProps {
  file: AudioFile | null;
  allFiles: AudioFile[];
  onClose: () => void;
  onRenamePatternSettings: () => void;
  onActivateFile?: (file: AudioFile) => void;
}

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#3b82f6', '#64748b'];

const DetailRow: React.FC<{ label: string; value: string | number | undefined }> = ({ label, value }) => (
    <div className="py-2.5 border-b border-slate-200/50 dark:border-slate-800/50 last:border-0 flex justify-between items-center group hover:bg-slate-50 dark:hover:bg-slate-800/30 px-2 rounded transition-colors">
        <dt className="text-xs font-semibold text-slate-500 dark:text-slate-500 uppercase tracking-wide">{label}</dt>
        <dd className="text-sm font-medium text-slate-900 dark:text-slate-200 text-right truncate max-w-[60%]">{value || '-'}</dd>
    </div>
);

const EnergyBar: React.FC<{ label: string; value: number | undefined; colorClass: string }> = ({ label, value, colorClass }) => {
    const safeValue = Math.min(Math.max(value || 0, 0), 10);
    return (
        <div className="py-2">
            <div className="flex justify-between mb-1.5 items-end">
                <span className="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider">{label}</span>
                <span className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300">{safeValue}/10</span>
            </div>
            <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <div 
                    className={`h-full rounded-full transition-all duration-1000 ease-out ${colorClass} relative`} 
                    style={{ width: `${(safeValue / 10) * 100}%` }}
                >
                    <div className="absolute inset-0 bg-white/20"></div>
                </div>
            </div>
        </div>
    );
};

const RightPanel: React.FC<RightPanelProps> = ({ file, allFiles, onClose, onRenamePatternSettings, onActivateFile }) => {
  
  // -- Statistics Calculation --
  const stats = useMemo(() => {
    if (allFiles.length === 0) return null;

    const genreCounts = _.countBy(allFiles, (f: AudioFile) => {
        const g = (f.fetchedTags?.genre || f.originalTags?.genre || 'Nieznany').toLowerCase();
        return g.charAt(0).toUpperCase() + g.slice(1);
    });
    
    const genreData = Object.entries(genreCounts)
        .map(([name, value]) => ({ name, value }))
        .sort((a: any, b: any) => b.value - a.value)
        .slice(0, 8);

    return { genreData, total: allFiles.length };
  }, [allFiles]);

  // -- Harmonic Suggestions --
  const suggestions = useMemo(() => {
      if (!file) return [];
      return findMixSuggestions(file, allFiles).slice(0, 5); // Top 5
  }, [file, allFiles]);


  // -- No File Selected View (Library Stats) --
  if (!file) {
      return (
          <aside className="w-80 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 flex flex-col h-full overflow-y-auto scrollbar-thin">
             <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-indigo-500" viewBox="0 0 20 20" fill="currentColor"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" /></svg>
                        Statystyki
                    </h2>
                    <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-500 px-2 py-1 rounded-full">Biblioteka</span>
                </div>
                
                {stats && stats.total > 0 ? (
                    <div className="space-y-8 animate-fade-in">
                        <div className="grid grid-cols-2 gap-3">
                             <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 text-white p-4 rounded-xl shadow-lg shadow-indigo-500/20 text-center">
                                <div className="text-3xl font-extrabold tracking-tight">{stats.total}</div>
                                <div className="text-[10px] uppercase font-bold opacity-80 mt-1">Utworów</div>
                             </div>
                             <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-sm text-center hover:bg-slate-50 dark:hover:bg-slate-700/50 transition cursor-pointer group" onClick={onRenamePatternSettings}>
                                <div className="flex justify-center mb-1 text-slate-400 group-hover:text-indigo-500 transition-colors">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                </div>
                                <div className="text-[10px] uppercase font-bold text-slate-500 group-hover:text-slate-700 dark:group-hover:text-slate-300">Wzór Nazw</div>
                             </div>
                        </div>

                        {stats.genreData.length > 0 && (
                            <div>
                                <h3 className="text-xs font-bold text-slate-400 uppercase mb-4 tracking-wider pl-1">Gatunki</h3>
                                <div className="h-48 w-full bg-slate-50 dark:bg-slate-800/30 rounded-lg p-2">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={stats.genreData}
                                                innerRadius={40}
                                                outerRadius={70}
                                                paddingAngle={5}
                                                dataKey="value"
                                                stroke="none"
                                            >
                                                {stats.genreData.map((entry: any, index: number) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip 
                                                contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff', fontSize: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }} 
                                                itemStyle={{ color: '#fff' }}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-center p-6">
                        <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                        </div>
                        <p className="text-sm text-slate-500">Biblioteka jest pusta.</p>
                        <p className="text-xs text-slate-400 mt-1">Zaimportuj utwory, aby zobaczyć analizę.</p>
                    </div>
                )}
             </div>
          </aside>
      );
  }

  // -- Single File Selected View --
  const tags = file.fetchedTags || file.originalTags || {};

  return (
    <aside className="w-80 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 flex flex-col h-full overflow-y-auto scrollbar-thin">
      
      {/* 1. Header & Cover */}
      <div className="relative">
          <div className="aspect-square w-full relative group">
                <AlbumCover tags={tags} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-90"></div>
                
                <div className="absolute bottom-0 left-0 right-0 p-5">
                    <h2 className="text-xl font-bold text-white leading-tight drop-shadow-md line-clamp-2" title={tags.title}>{tags.title || file.file.name}</h2>
                    <p className="text-indigo-300 font-medium text-sm mt-1 drop-shadow-sm truncate">{tags.artist || 'Unknown Artist'}</p>
                </div>
          </div>
      </div>

      <div className="p-6 space-y-6">
        
        {/* 2. DJ Performance Card */}
        <div className="bg-slate-900 rounded-xl p-4 shadow-lg border border-slate-700/50 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-20 h-20 bg-indigo-500/10 rounded-full -mr-10 -mt-10 blur-xl"></div>
            
            <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-3 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
                DJ Performance
            </div>
            
            <div className="flex divide-x divide-slate-700">
                <div className="flex-1 text-center pr-2">
                    <div className="text-3xl font-black text-white tracking-tighter">{tags.bpm || <span className="text-slate-600 text-2xl">---</span>}</div>
                    <div className="text-[10px] text-slate-400 uppercase mt-1">BPM</div>
                </div>
                <div className="flex-1 text-center pl-2">
                    <div className="text-3xl font-black text-indigo-400 tracking-tighter">{tags.initialKey || <span className="text-slate-600 text-2xl">--</span>}</div>
                    <div className="text-[10px] text-slate-400 uppercase mt-1">Key (Camelot)</div>
                </div>
            </div>
        </div>

        {/* 3. Harmonic Mixing Suggestions */}
        {suggestions.length > 0 && (
            <div>
                <div className="flex items-center justify-between mb-3 pl-1">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Sugestie Miksu</h3>
                    <span className="text-[10px] bg-green-500/10 text-green-500 px-1.5 py-0.5 rounded font-bold">MATCH</span>
                </div>
                <div className="space-y-2">
                    {suggestions.map(s => (
                        <div 
                            key={s.id} 
                            onClick={() => onActivateFile && onActivateFile(s)}
                            className="flex items-center bg-slate-50 dark:bg-slate-800/50 p-2 rounded-lg cursor-pointer hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors border border-transparent hover:border-indigo-200 dark:hover:border-indigo-800"
                        >
                            <AlbumCover tags={s.fetchedTags || s.originalTags} className="w-8 h-8 rounded mr-3" />
                            <div className="flex-1 overflow-hidden">
                                <div className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">{(s.fetchedTags?.title || s.originalTags.title || s.file.name)}</div>
                                <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate flex items-center">
                                    <span className="font-mono text-indigo-500 mr-2">{(s.fetchedTags?.initialKey || s.originalTags.initialKey)}</span>
                                    {(s.fetchedTags?.bpm || s.originalTags.bpm)} BPM
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}

        {/* 4. Energy Levels */}
        <div>
            <EnergyBar label="Energia" value={tags.energy} colorClass="bg-gradient-to-r from-orange-400 to-red-500" />
            <EnergyBar label="Taneczność" value={tags.danceability} colorClass="bg-gradient-to-r from-indigo-400 to-purple-500" />
        </div>

        {/* 5. Metadata List */}
        <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase mb-3 pl-1">Metadane</h3>
            <div className="bg-slate-50 dark:bg-slate-800/30 rounded-lg p-2 border border-slate-100 dark:border-slate-800">
                <DetailRow label="Album" value={tags.album} />
                <DetailRow label="Gatunek" value={tags.genre} />
                <DetailRow label="Rok" value={tags.year} />
                <DetailRow label="Typ" value={file.file.type.split('/')[1]?.toUpperCase()} />
                <DetailRow label="Rozmiar" value={`${(file.file.size / (1024*1024)).toFixed(2)} MB`} />
            </div>
        </div>

        <button 
            onClick={onClose}
            className="w-full py-2 text-xs font-bold text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 uppercase tracking-widest transition-colors"
        >
            Zamknij Panel
        </button>
      </div>
    </aside>
  );
};

export default RightPanel;
