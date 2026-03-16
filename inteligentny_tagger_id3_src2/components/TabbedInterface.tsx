

import React from 'react';

export interface Tab {
  id: string;
  label: string;
  component: React.ReactNode;
}

interface TabbedInterfaceProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

const TabbedInterface: React.FC<TabbedInterfaceProps> = ({ tabs, activeTab, onTabChange }) => {
  const activeComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div>
      <div className="border-b border-slate-300 dark:border-slate-700">
        <nav className="-mb-px flex space-x-6" aria-label="Tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`${
                activeTab === tab.id
                  ? 'border-indigo-500 dark:border-indigo-400 text-indigo-600 dark:text-indigo-300'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300 dark:hover:border-slate-600'
              } whitespace-nowrap py-3 px-1 border-b-2 font-bold text-sm transition-colors focus:outline-none`}
              aria-current={activeTab === tab.id ? 'page' : undefined}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="pt-6">
        {activeComponent}
      </div>
    </div>
  );
};

export default TabbedInterface;