import React from "react";
import { Playlist } from "../types";

interface SidebarItemProps {
  icon: React.ReactNode;
  label: string;
  isActive?: boolean;
  onClick?: () => void;
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  icon,
  label,
  isActive,
  onClick,
}) => (
  <div
    onClick={onClick}
    className={`
      relative group flex flex-col items-center justify-center py-4 cursor-pointer transition-all duration-300
      ${
        isActive
          ? "text-[var(--accent-cyan)]"
          : "text-[var(--text-muted)] hover:text-white"
      }
    `}
  >
    {isActive && (
      <>
        <div className="absolute left-0 top-2 bottom-2 w-1 bg-[var(--accent-cyan)] glow-cyan rounded-r-full shadow-[0_0_15px_var(--accent-cyan)]"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent-cyan)]/10 to-transparent"></div>
      </>
    )}
    <div className={`relative z-10 transition-transform duration-300 ${isActive ? "scale-110" : "group-hover:scale-105"}`}>
      {icon}
    </div>
    <span className="text-[10px] uppercase font-bold tracking-tighter mt-1 opacity-0 group-hover:opacity-100 transition-opacity absolute -right-20 bg-[var(--bg-surface)] px-2 py-1 rounded border border-white/10 pointer-events-none z-50 whitespace-nowrap">
      {label}
    </span>
  </div>
);

interface SidebarProps {
  activePlaylistId: string | null;
  onPlaylistSelect: (id: string | null) => void;
  onShowRecentlyAdded: () => void;
  onShowDuplicates: () => void;
  onSettings: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  activePlaylistId,
  onPlaylistSelect,
  onShowRecentlyAdded,
  onShowDuplicates,
  onSettings,
}) => {
  return (
    <aside className="w-20 glass-effect border-r border-white/5 flex flex-col h-full items-center py-6 flex-shrink-0 z-30">
      <div className="mb-10 text-[var(--accent-magenta)] glow-magenta p-2 rounded-xl bg-magenta-500/10 border border-magenta-500/20">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2H2v10a10 10 0 0 0 10 10V12h10a10 10 0 0 0-10-10Z"/>
          <path d="M12 2a10 10 0 0 1 10 10"/>
        </svg>
      </div>

      <div className="flex-grow flex flex-col w-full">
        <SidebarItem
          label="Home"
          isActive={activePlaylistId === 'dashboard'}
          onClick={() => onPlaylistSelect('dashboard')}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10z" /></svg>}
        />
        <SidebarItem
          label="Biblioteka"
          isActive={activePlaylistId === null}
          onClick={() => onPlaylistSelect(null)}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>}
        />
        <SidebarItem
          label="Utwory"
          isActive={false}
          onClick={onShowRecentlyAdded}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 6l12-3" /></svg>}
        />
        <SidebarItem
          label="Przeglądarka"
          isActive={activePlaylistId === 'browser'}
          onClick={() => onPlaylistSelect('browser')}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>}
        />
        <SidebarItem
          label="Duplikaty"
          onClick={onShowDuplicates}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
        />
        <SidebarItem
          label="Ustawienia"
          onClick={onSettings}
          icon={<svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>}
        />
      </div>

      <div className="mt-auto items-center flex flex-col gap-4 pb-4">
        <div className="w-10 h-10 rounded-full border border-white/10 glow-cyan flex items-center justify-center overflow-hidden">
           <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="avatar" />
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
