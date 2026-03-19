

import React from 'react';

const PlaceholderTab: React.FC<{ title: string; description?: string }> = ({ title, description }) => (
  <div className="text-center p-10 bg-slate-100 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700 animate-fade-in">
    <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-200">{title}</h2>
    <p className="text-slate-500 dark:text-slate-400 mt-2">{description || 'Ta funkcja jest w przygotowaniu i będzie dostępna wkrótce.'}</p>
  </div>
);

export default PlaceholderTab;