import React from "react";
import DirectoryConnect from "./DirectoryConnect"; // Nowy komponent
import Roadmap from "./Roadmap"; // Nowy komponent

interface WelcomeScreenProps {
  children: React.ReactNode; // To będzie FileDropzone
  onDirectoryConnect: (handle: any) => void;
}


const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  children,
  onDirectoryConnect,
}) => {
  const isFileSystemAccessSupported = "showDirectoryPicker" in window;

  return (
    <div className="flex flex-col items-center justify-center max-w-4xl w-full space-y-12 animate-fade-in text-center px-6 mt-12 mb-20">
      <div className="space-y-4">
        <div className="w-20 h-20 bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-blue)] rounded-3xl mx-auto flex items-center justify-center shadow-2xl glow-cyan">
           <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 6l12-3" />
           </svg>
        </div>
        <h2 className="text-5xl font-extrabold text-white font-heading tracking-tight">Audio AI Studio</h2>
        <p className="text-white/40 font-medium max-w-lg mx-auto">Przenieś swoją bibliotekę muzyczną na wyższy poziom dzięki zaawansowanej analizie AI i automatycznemu tagowaniu.</p>
      </div>

      <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
        <div className="glass-effect rounded-[2.5rem] p-8 border border-white/5 space-y-6 flex flex-col h-full text-left">
           <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-[var(--accent-cyan)]">
                 <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                 </svg>
              </div>
              <h3 className="text-lg font-bold text-white uppercase tracking-tight">Importuj Pliki</h3>
           </div>
           
           <div className="flex-1">
              {children}
           </div>

           <p className="text-[10px] text-white/20 uppercase font-bold tracking-widest text-center">Wgrywasz pliki do pamięci przeglądarki</p>
        </div>

        <div className="glass-effect rounded-[2.5rem] p-8 border border-white/5 space-y-6 flex flex-col h-full text-left">
           <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-[var(--accent-magenta)]">
                 <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                 </svg>
              </div>
              <h3 className="text-lg font-bold text-white uppercase tracking-tight">Tryb Folderu</h3>
           </div>

           <div className="flex-1 space-y-4">
              <p className="text-sm text-white/50 leading-relaxed">
                Połącz się bezpośrednio z folderem na dysku. <span className="text-[var(--accent-cyan)] font-bold">Pełna kontrola</span> i natychmiastowy zapis.
              </p>
              
              {isFileSystemAccessSupported && (
                 <DirectoryConnect onDirectoryConnect={onDirectoryConnect} />
              )}
           </div>

           <div className="pt-4 border-t border-white/5">
              <div className="flex items-center gap-2 text-[10px] text-[var(--accent-magenta)] font-bold uppercase tracking-wider">
                 <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent-magenta)] animate-pulse shadow-[0_0_8px_var(--accent-magenta)]"></div>
                 Eksperymentalny Tryb Bezpośredni
              </div>
           </div>
        </div>
      </div>

      <Roadmap />
    </div>
  );
};

export default WelcomeScreen;
