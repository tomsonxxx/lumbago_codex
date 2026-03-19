

import React from 'react';

interface MainToolbarProps {
  onTabChange: (tabId: string) => void;
}

const MainToolbar: React.FC<MainToolbarProps> = ({ onTabChange }) => {
  // Styl zgodny z prośbą: gradienty #39ff14->#00ff88
  const buttonStyle = "bg-gradient-to-br from-[#39ff14] to-[#00ff88] text-slate-900 rounded-lg px-4 py-2 text-sm font-bold hover:opacity-90 transition-opacity shadow-md";

  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      <button className={buttonStyle} onClick={() => onTabChange('scan')}>
        Import / Skan
      </button>
      <button className={buttonStyle} onClick={() => onTabChange('tagger')}>
        Smart Tagger AI
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