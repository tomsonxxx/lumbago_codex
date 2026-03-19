
import React from 'react';
import { ID3Tags } from '../types';
import AlbumCover from './AlbumCover';

interface TagPreviewTooltipProps {
  originalTags: ID3Tags;
  fetchedTags?: ID3Tags;
}

// Helper to normalize values for comparison (treat undefined/null as empty string)
const normalize = (val: any) => {
    if (val === undefined || val === null) return '';
    return String(val).trim();
};

interface TagDetailLineProps {
    label: string;
    value?: string | number;
    originalValue?: string | number; // Pass original value to compare
    variant?: 'original' | 'new';
}

const TagDetailLine: React.FC<TagDetailLineProps> = ({ label, value, originalValue, variant = 'new' }) => {
  const normValue = normalize(value);
  const normOriginal = normalize(originalValue);
  const isChanged = variant === 'new' && normValue !== normOriginal && normValue !== '';
  
  let valueClasses = "truncate break-words flex-1";
  let containerClasses = "flex items-baseline gap-2 text-xs py-0.5 rounded px-1 -mx-1 transition-colors";
  
  if (variant === 'new') {
      if (isChanged) {
          valueClasses += " text-green-700 dark:text-green-300 font-bold";
          containerClasses += " bg-green-50 dark:bg-green-900/30";
      } else {
          valueClasses += " text-slate-700 dark:text-slate-300";
      }
  } else {
      // Original Variant
      if (normalize(value) !== normalize(originalValue) && variant === 'original') {
           // Logic handled in parent mostly, but for 'original' variant we imply it's the source
           valueClasses += " text-slate-500 dark:text-slate-400";
      } else {
           valueClasses += " text-slate-500 dark:text-slate-400";
      }
  }

  return (
    <div className={containerClasses} title={String(value)}>
      <span className="font-semibold text-slate-500 dark:text-slate-400 whitespace-nowrap min-w-[70px]">{label}:</span> 
      <span className={valueClasses}>
          {value ?? <span className="opacity-30 italic text-[10px]">brak</span>}
      </span>
      {isChanged && (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-green-500 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
      )}
    </div>
  );
};

const TagPreviewTooltip: React.FC<TagPreviewTooltipProps> = ({ originalTags, fetchedTags }) => {
  if (!fetchedTags) return null;

  const hasCoverChanged = normalize(originalTags.albumCoverUrl) !== normalize(fetchedTags.albumCoverUrl) && !!fetchedTags.albumCoverUrl;

  return (
    <div className="absolute z-50 w-[48rem] max-w-[90vw] p-4 -mt-24 left-16 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-2xl animate-fade-in pointer-events-none ring-1 ring-black/5">
      
      {/* Header */}
      <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate-100 dark:border-slate-700/50">
          <div className="flex items-center gap-2">
              <div className="bg-indigo-100 dark:bg-indigo-900/50 p-1 rounded text-indigo-600 dark:text-indigo-400">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" /></svg>
              </div>
              <span className="text-xs font-bold text-slate-700 dark:text-slate-200 uppercase tracking-wider">Podgląd zmian AI</span>
          </div>
      </div>

      <div className="flex space-x-0 divide-x divide-slate-100 dark:divide-slate-700">
        
        {/* Original Tags Column */}
        <div className="w-1/2 pr-4 opacity-70">
          <h5 className="text-xs font-bold text-slate-500 dark:text-slate-400 mb-3 uppercase">Oryginał</h5>
          <div className="flex space-x-3 mb-4">
             <div className="w-16 h-16 flex-shrink-0 bg-slate-100 dark:bg-slate-700 rounded-md overflow-hidden flex items-center justify-center grayscale opacity-70">
                {originalTags.albumCoverUrl ? (
                    <img src={originalTags.albumCoverUrl} className="w-full h-full object-cover" alt="" />
                ) : (
                    <span className="text-[9px] text-slate-400">Brak</span>
                )}
             </div>
             <div className="space-y-1 flex-grow min-w-0">
                <TagDetailLine label="Tytuł" value={originalTags.title} variant="original" />
                <TagDetailLine label="Artysta" value={originalTags.artist} variant="original" />
             </div>
          </div>
          <div className="space-y-1">
            <TagDetailLine label="Album" value={originalTags.album} variant="original" />
            <TagDetailLine label="Rok" value={originalTags.year} variant="original" />
            <TagDetailLine label="Gatunek" value={originalTags.genre} variant="original" />
            <TagDetailLine label="BPM" value={originalTags.bpm} variant="original" />
            <TagDetailLine label="Klucz" value={originalTags.initialKey} variant="original" />
          </div>
        </div>
        
        {/* Fetched Tags Column */}
        <div className="w-1/2 pl-4">
          <h5 className="text-xs font-bold text-indigo-600 dark:text-indigo-400 mb-3 uppercase flex items-center gap-2">
              Po zmianach
              <span className="bg-green-100 text-green-700 text-[9px] px-1.5 py-0.5 rounded-full normal-case">Gemini AI</span>
          </h5>
          <div className="flex space-x-3 mb-4">
             <div className="relative w-16 h-16 flex-shrink-0">
                <AlbumCover tags={fetchedTags} className="w-full h-full shadow-sm border border-slate-100 dark:border-slate-600 rounded-md" />
                {hasCoverChanged && (
                    <div className="absolute -top-2 -right-2 bg-green-500 text-white p-0.5 rounded-full border-2 border-white dark:border-slate-800 shadow-sm">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                    </div>
                )}
             </div>
             <div className="space-y-1 overflow-hidden flex-grow min-w-0">
                <TagDetailLine label="Tytuł" value={fetchedTags.title} originalValue={originalTags.title} variant="new" />
                <TagDetailLine label="Artysta" value={fetchedTags.artist} originalValue={originalTags.artist} variant="new" />
             </div>
          </div>
           <div className="space-y-1">
                <TagDetailLine label="Album" value={fetchedTags.album} originalValue={originalTags.album} variant="new" />
                <TagDetailLine label="Rok" value={fetchedTags.year} originalValue={originalTags.year} variant="new" />
                <TagDetailLine label="Gatunek" value={fetchedTags.genre} originalValue={originalTags.genre} variant="new" />
                <TagDetailLine label="BPM" value={fetchedTags.bpm} originalValue={originalTags.bpm} variant="new" />
                <TagDetailLine label="Klucz" value={fetchedTags.initialKey} originalValue={originalTags.initialKey} variant="new" />
                <div className="pt-2 mt-2 border-t border-slate-100 dark:border-slate-700/50">
                    <TagDetailLine label="Label" value={fetchedTags.copyright} originalValue={originalTags.copyright} variant="new" />
                </div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(TagPreviewTooltip);
