import React from 'react';
import { ProcessingState } from '../types';

// Ulepszona, deklaratywna mapa do zarządzania statusami
const statusDetailsMap: Record<ProcessingState, { icon: React.ReactNode; text: string; color: string }> = {
  [ProcessingState.PENDING]: {
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    text: 'Oczekuje',
    color: 'text-slate-500',
  },
  [ProcessingState.PROCESSING]: {
    icon: (
      <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    ),
    text: 'Przetwarzanie',
    color: 'text-indigo-400',
  },
  [ProcessingState.DOWNLOADING]: {
    icon: (
       <svg className="animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
         <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
         <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
       </svg>
    ),
    text: 'Zapisywanie / Pobieranie',
    color: 'text-indigo-400',
  },
  [ProcessingState.SUCCESS]: {
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    text: 'Sukces',
    color: 'text-green-500',
  },
  [ProcessingState.ERROR]: {
    icon: (
      <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    text: 'Błąd',
    color: 'text-red-500',
  },
};

export const StatusIcon: React.FC<{ state: ProcessingState }> = ({ state }) => {
  const details = statusDetailsMap[state];

  if (!details) {
    return null;
  }

  const { icon, text, color } = details;
  
  const baseClasses = "w-6 h-6 mr-4 flex-shrink-0 transition-colors duration-300";

  // Zwraca ikonę opakowaną w div dla lepszej dostępności (tooltip) i spójności.
  return (
    <div title={text} className={`${baseClasses} ${color}`}>
        {icon}
    </div>
  );
};