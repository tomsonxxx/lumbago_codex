import React from 'react';

const SidebarItem: React.FC<{ icon: React.ReactNode; label: string; isActive?: boolean; count?: number }> = ({ icon, label, isActive, count }) => (
  <div className={`flex items-center justify-between px-4 py-2 mx-2 rounded-md cursor-pointer transition-colors group ${isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>
    <div className="flex items-center">
      <span className={`${isActive ? 'text-white' : 'text-slate-500 group-hover:text-white'}`}>{icon}</span>
      <span className="ml-3 text-sm font-medium">{label}</span>
    </div>
    {count !== undefined && (
      <span className={`text-xs ${isActive ? 'text-indigo-200' : 'text-slate-600 group-hover:text-slate-400'}`}>{count}</span>
    )}
  </div>
);

interface SidebarProps {
  totalFiles?: number;
}

const Sidebar: React.FC<SidebarProps> = ({ totalFiles }) => {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full flex-shrink-0">
      <div className="p-4 flex items-center space-x-2 border-b border-slate-800 mb-2">
        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
                <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
            </svg>
        </div>
        <span className="text-white font-bold text-lg tracking-tight">Lumbago AI</span>
      </div>

      <div className="flex-grow overflow-y-auto py-2 space-y-1">
        <div className="px-4 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Biblioteka</div>
        <SidebarItem 
            isActive={true}
            count={totalFiles || 0}
            label="Kolekcja" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>} 
        />
        <SidebarItem 
            label="Playlisty" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>} 
        />
        <SidebarItem 
            label="Historia" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>} 
        />

        <div className="px-4 py-2 mt-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Analiza</div>
        <SidebarItem 
            label="Duplikaty" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>} 
        />
        <SidebarItem 
            label="Raporty AI" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>} 
        />
        
        <div className="px-4 py-2 mt-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Integracje</div>
        <SidebarItem 
            label="Rekordbox XML" 
            icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>} 
        />
      </div>

      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-800 rounded-lg p-3">
             <div className="text-xs font-bold text-slate-400 mb-1">Status AI</div>
             <div className="flex items-center space-x-2">
                 <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                 <span className="text-xs text-slate-300">Gotowy do pracy</span>
             </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;