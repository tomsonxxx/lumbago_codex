
import React from 'react';

interface StartScreenProps {
  onNavigate: (view: string) => void;
  onImport: () => void;
}

const ActionCard: React.FC<{ 
  icon: React.ReactNode; 
  label: string; 
  desc: string; 
  color: 'cyan' | 'pink' | 'green';
  onClick: () => void;
}> = ({ icon, label, desc, color, onClick }) => {
  const colorClasses = {
    cyan: "hover:border-cyan-400/50 hover:shadow-[0_0_20px_rgba(34,211,238,0.2)] group-hover:text-cyan-400",
    pink: "hover:border-fuchsia-400/50 hover:shadow-[0_0_20px_rgba(232,121,249,0.2)] group-hover:text-fuchsia-400",
    green: "hover:border-[#39ff14]/50 hover:shadow-[0_0_20px_rgba(57,255,20,0.2)] group-hover:text-[#39ff14]"
  };

  return (
    <button 
      onClick={onClick}
      className={`group relative flex flex-col items-start p-6 rounded-2xl bg-[#1a1a2e]/60 border border-white/5 backdrop-blur-sm transition-all duration-300 text-left w-full h-full ${colorClasses[color]}`}
    >
      <div className={`mb-4 p-3 rounded-xl bg-white/5 transition-colors ${colorClasses[color]}`}>
        {icon}
      </div>
      <h3 className="text-lg font-bold text-white mb-1 group-hover:translate-x-1 transition-transform">{label}</h3>
      <p className="text-sm text-slate-400 group-hover:text-slate-300">{desc}</p>
      
      {/* Decorative Line */}
      <div className={`absolute bottom-0 left-6 right-6 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:via-${color === 'green' ? '[#39ff14]' : color === 'pink' ? 'fuchsia-500' : 'cyan-500'} transition-all`}></div>
    </button>
  );
};

const StartScreen: React.FC<StartScreenProps> = ({ onNavigate, onImport }) => {
  return (
    <div className="flex flex-col h-full overflow-y-auto custom-scrollbar p-6 md:p-10 relative">
      {/* Background Decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none"></div>
      
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center py-10 md:py-20 relative z-10 text-center animate-fade-in">
        <div className="mb-6 relative">
            <div className="absolute inset-0 bg-cyan-500 blur-[40px] opacity-20 animate-pulse-glow"></div>
            <h1 className="text-5xl md:text-7xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-white to-fuchsia-500 tracking-tighter filter drop-shadow-[0_0_10px_rgba(255,255,255,0.3)]">
              LUMBAGO AI
            </h1>
        </div>
        <p className="text-slate-400 text-lg md:text-xl max-w-2xl mb-8">
          Inteligentne centrum zarządzania biblioteką muzyczną.
          <br/>Tagowanie, organizacja i analiza w jednym miejscu.
        </p>
        
        <button 
          onClick={() => onNavigate('library')}
          className="group px-8 py-3 bg-white text-black font-bold rounded-full hover:scale-105 transition-transform flex items-center gap-2 shadow-[0_0_20px_rgba(255,255,255,0.3)]"
        >
          <span>Otwórz Bibliotekę</span>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
        </button>
      </div>

      {/* Actions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 max-w-6xl mx-auto w-full relative z-10 animate-slide-up">
        <ActionCard 
          color="cyan"
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>}
          label="Importuj Pliki"
          desc="Dodaj nowe utwory, foldery lub linki do biblioteki."
          onClick={onImport}
        />
        <ActionCard 
          color="pink"
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
          label="Smart Tagger"
          desc="Automatyczne uzupełnianie metadanych przez AI."
          onClick={() => onNavigate('tagger')}
        />
        <ActionCard 
          color="green"
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
          label="Duplikaty"
          desc="Znajdź i usuń powtarzające się utwory."
          onClick={() => onNavigate('duplicates')}
        />
        <ActionCard 
          color="cyan"
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>}
          label="Konwerter XML"
          desc="Importuj bazy z Rekordbox lub VirtualDJ."
          onClick={() => onNavigate('converter')}
        />
      </div>

      {/* Footer Info */}
      <div className="mt-auto pt-10 text-center text-slate-500 text-xs">
        <p>Lumbago Music AI v3.0 • Powered by Gemini Pro</p>
      </div>
    </div>
  );
};

export default StartScreen;
