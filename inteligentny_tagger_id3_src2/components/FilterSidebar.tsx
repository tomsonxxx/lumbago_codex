
import React, { useMemo } from 'react';
import { AudioFile, ProcessingState } from '../types';

interface FilterSidebarProps {
  files: AudioFile[];
  filters: {
    genre: string | null;
    year: string | null;
    status: ProcessingState | null | 'PROCESSED';
  };
  onFilterChange: (key: 'genre' | 'year' | 'status', value: any) => void;
  isOpen: boolean;
  onClose: () => void;
}

const FilterSidebar: React.FC<FilterSidebarProps> = ({ files, filters, onFilterChange, isOpen, onClose }) => {
  // Wyciąganie unikalnych wartości dla filtrów
  const uniqueGenres = useMemo(() => {
    const genres = new Set<string>();
    files.forEach(f => {
      const g = f.fetchedTags?.genre || f.originalTags?.genre;
      if (g) genres.add(g);
    });
    return Array.from(genres).sort();
  }, [files]);

  const uniqueYears = useMemo(() => {
    const years = new Set<string>();
    files.forEach(f => {
      const y = f.fetchedTags?.year || f.originalTags?.year;
      if (y) years.add(y);
    });
    return Array.from(years).sort().reverse();
  }, [files]);

  const sidebarClasses = `fixed inset-y-0 right-0 z-40 w-80 bg-white dark:bg-slate-900 shadow-2xl transform transition-transform duration-300 ease-in-out border-l border-slate-200 dark:border-slate-700 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`;

  return (
    <>
        {/* Overlay na mobile */}
        {isOpen && (
            <div className="fixed inset-0 bg-black/50 z-30 md:hidden" onClick={onClose}></div>
        )}
        
        <div className={sidebarClasses}>
          <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
            <h3 className="text-lg font-bold text-slate-800 dark:text-white flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                Filtrowanie
            </h3>
            <button onClick={onClose} className="p-1 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          <div className="p-4 overflow-y-auto h-[calc(100%-64px)] space-y-6">
            
            {/* Status Filter */}
            <div>
                <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-2 uppercase tracking-wider">Status</h4>
                <div className="space-y-2">
                    {[
                        { label: 'Wszystkie', value: null },
                        { label: 'Przetworzone (Sukces)', value: ProcessingState.SUCCESS },
                        { label: 'Błędy', value: ProcessingState.ERROR },
                        { label: 'Oczekujące', value: ProcessingState.PENDING },
                    ].map((opt) => (
                        <label key={opt.label} className="flex items-center space-x-2 cursor-pointer group">
                             <input 
                                type="radio" 
                                name="status" 
                                checked={filters.status === opt.value}
                                onChange={() => onFilterChange('status', opt.value)}
                                className="text-indigo-600 focus:ring-indigo-500 bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-600"
                             />
                             <span className={`text-sm group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors ${filters.status === opt.value ? 'font-medium text-indigo-700 dark:text-indigo-300' : 'text-slate-600 dark:text-slate-400'}`}>
                                 {opt.label}
                             </span>
                        </label>
                    ))}
                </div>
            </div>

            <div className="border-t border-slate-200 dark:border-slate-700 pt-4"></div>

            {/* Genre Filter */}
            <div>
                 <div className="flex justify-between items-center mb-2">
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wider">Gatunek</h4>
                    {filters.genre && <button onClick={() => onFilterChange('genre', null)} className="text-xs text-indigo-500 hover:underline">Wyczyść</button>}
                 </div>
                 {uniqueGenres.length > 0 ? (
                    <div className="max-h-48 overflow-y-auto space-y-1 custom-scrollbar pr-1">
                        {uniqueGenres.map(genre => (
                            <button
                                key={genre}
                                onClick={() => onFilterChange('genre', filters.genre === genre ? null : genre)}
                                className={`w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors ${filters.genre === genre ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-medium' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
                            >
                                {genre}
                            </button>
                        ))}
                    </div>
                 ) : (
                     <p className="text-xs text-slate-400 italic">Brak gatunków w bibliotece.</p>
                 )}
            </div>

            <div className="border-t border-slate-200 dark:border-slate-700 pt-4"></div>

            {/* Year Filter */}
            <div>
                 <div className="flex justify-between items-center mb-2">
                    <h4 className="text-sm font-semibold text-slate-900 dark:text-white uppercase tracking-wider">Rok</h4>
                    {filters.year && <button onClick={() => onFilterChange('year', null)} className="text-xs text-indigo-500 hover:underline">Wyczyść</button>}
                 </div>
                 {uniqueYears.length > 0 ? (
                     <div className="flex flex-wrap gap-2">
                         {uniqueYears.map(year => (
                             <button
                                key={year}
                                onClick={() => onFilterChange('year', filters.year === year ? null : year)}
                                className={`px-2.5 py-1 rounded-full text-xs border transition-all ${filters.year === year ? 'bg-indigo-600 border-indigo-600 text-white shadow-md' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-indigo-300 dark:hover:border-indigo-700'}`}
                             >
                                 {year}
                             </button>
                         ))}
                     </div>
                 ) : (
                     <p className="text-xs text-slate-400 italic">Brak informacji o roku.</p>
                 )}
            </div>
            
          </div>
        </div>
    </>
  );
};

export default FilterSidebar;
