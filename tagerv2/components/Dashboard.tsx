import React from "react";

interface DashboardProps {
  totalFiles: number;
  onImport: () => void;
  onFindDuplicates: () => void;
  onAnalyzeAll: () => void;
  popularTags?: string[];
  onTagClick?: (tag: string) => void;
  onBatchEdit?: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  totalFiles,
  onImport,
  onFindDuplicates,
  onAnalyzeAll,
  onBatchEdit,
  popularTags = [],
  onTagClick,
}) => {
  return (
    <div className="flex-grow overflow-y-auto p-12 space-y-12 animate-fade-in scrollbar-hide">
      <div className="flex flex-col gap-2">
        <h2 className="text-4xl font-bold text-white font-heading">Witaj z powrotem!</h2>
        <p className="text-white/40 font-medium italic">Twoja inteligentna biblioteka muzyczna jest gotowa.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Stats Panel */}
        <div className="lg:col-span-2 glass-effect rounded-[2.5rem] p-8 border border-white/5 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent-cyan)]/10 rounded-full -mr-32 -mt-32 blur-[80px] group-hover:bg-[var(--accent-cyan)]/20 transition-all duration-700"></div>
          <div className="relative z-10 space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-white/30">Status Biblioteki</h3>
            <div className="flex items-end gap-2">
              <span className="text-7xl font-bold text-white leading-none">{totalFiles}</span>
              <span className="text-xl font-bold text-[var(--accent-cyan)] glow-cyan mb-2">Utworów</span>
            </div>
            <div className="pt-8 grid grid-cols-3 gap-4">
               <div>
                  <p className="text-[10px] uppercase font-bold text-white/20 mb-1">Pojemność</p>
                  <p className="text-xl font-bold text-white">~4.2 GB</p>
               </div>
               <div>
                  <p className="text-[10px] uppercase font-bold text-white/20 mb-1">Gatunków</p>
                  <p className="text-xl font-bold text-white">12</p>
               </div>
               <div>
                  <p className="text-[10px] uppercase font-bold text-white/20 mb-1">Ostatni Skan</p>
                  <p className="text-xl font-bold text-white">Dzisiaj</p>
               </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="glass-effect rounded-[2.5rem] p-8 border border-white/5 flex flex-col gap-6">
           <h3 className="text-sm font-bold uppercase tracking-widest text-white/30">Szybkie Akcje</h3>
           
           <button 
             onClick={onImport}
             className="flex items-center gap-4 p-4 rounded-3xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 hover:scale-[1.02] active:scale-95 transition-all group"
           >
              <div className="p-3 rounded-2xl bg-[var(--accent-cyan)] text-black glow-cyan">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <div className="text-left">
                 <p className="text-sm font-bold text-white">Importuj Pliki</p>
                 <p className="text-[10px] text-white/40">Dodaj nową muzykę</p>
              </div>
           </button>

           <button 
             onClick={onAnalyzeAll}
             className="flex items-center gap-4 p-4 rounded-3xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 hover:scale-[1.02] active:scale-95 transition-all group"
           >
              <div className="p-3 rounded-2xl bg-[var(--accent-magenta)] text-white glow-magenta">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="text-left">
                 <p className="text-sm font-bold text-white">SMART AI Skan</p>
                 <p className="text-[10px] text-white/40">Automatyczne tagowanie</p>
              </div>
           </button>

           <button 
             onClick={onBatchEdit}
             className="flex items-center gap-4 p-4 rounded-3xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 hover:scale-[1.02] active:scale-95 transition-all group"
           >
              <div className="p-3 rounded-2xl bg-white/10 text-white">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              <div className="text-left">
                 <p className="text-sm font-bold text-white">Masowa Edycja</p>
                 <p className="text-[10px] text-white/40">Zmień tagi wielu plików</p>
              </div>
           </button>
        </div>
      </div>

      {/* Popular Tags Section */}
      <div className="glass-effect rounded-[2.5rem] p-8 border border-white/5 space-y-6">
        <h3 className="text-sm font-bold uppercase tracking-widest text-white/30">Najpopularniejsze Tagi (Top 15)</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
           {popularTags.slice(0, 15).map((tag, idx) => (
              <button
                key={tag}
                onClick={() => onTagClick?.(tag)}
                className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 hover:scale-[1.02] active:scale-95 transition-all group"
              >
                 <div className="flex items-center gap-3">
                    <span className="text-[10px] font-bold text-white/20">#{idx + 1}</span>
                    <span className="text-sm font-bold text-white group-hover:text-[var(--accent-cyan)] transition-colors">{tag}</span>
                 </div>
                 <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white/10 group-hover:text-[var(--accent-cyan)] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                 </svg>
              </button>
           ))}
           {popularTags.length === 0 && <p className="text-sm text-white/10 italic">Brak tagów do wyświetlenia. Zaimportuj pliki, aby zobaczyć statystyki.</p>}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
