

import React from 'react';

interface MainToolbarProps {
  onTabChange: (tabId: string) => void;
  onDirectorySelect: () => void;
}

const MainToolbar: React.FC<MainToolbarProps> = ({ onTabChange, onDirectorySelect }) => {
  // Styl zgodny z prośbą: gradienty #39ff14->#00ff88
  const buttonStyle = "bg-gradient-to-br from-[#39ff14] to-[#00ff88] text-slate-900 rounded-lg px-4 py-2 text-sm font-bold hover:opacity-90 transition-opacity shadow-md flex items-center gap-2";

  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      <button className={buttonStyle} onClick={onDirectorySelect}>
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" clipRule="evenodd" />
        </svg>
        Wybierz folder
      </button>
      <div className="h-6 w-px bg-slate-300 dark:bg-slate-700 mx-1"></div>
      <button className={buttonStyle} onClick={() => onTabChange('scan')}>
        Import / Skan
      </button>
      <button className={buttonStyle} onClick={() => onTabChange('dashboard')}>
        Dashboard
      </button>
      <button className={buttonStyle} onClick={() => onTabChange('tagger')}>
        SMART AI Skan
      </button>
      <button className={buttonStyle} onClick={() => onTabChange('converter')}>
        Konwerter XML
      </button>
      <button className={buttonStyle} onClick={() => onTabChange('duplicates')}>
        Wyszukiwarka Duplikatów
      </button>
    </div>
  );
};

export default MainToolbar;
