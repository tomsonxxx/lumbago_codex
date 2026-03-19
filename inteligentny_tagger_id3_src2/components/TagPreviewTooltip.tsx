import React from 'react';
import { ID3Tags } from '../types';
import AlbumCover from './AlbumCover';

interface TagPreviewTooltipProps {
  originalTags: ID3Tags;
  fetchedTags?: ID3Tags;
}

const TagDetailLine: React.FC<{ label: string; value?: string | number }> = ({ label, value }) => (
  <p className="text-xs text-slate-500 dark:text-slate-400 truncate" title={String(value)}>
    <span className="font-semibold text-slate-600 dark:text-slate-300">{label}:</span> {value ?? 'Brak'}
  </p>
);

const TagColumn: React.FC<{ title: string; tags: ID3Tags }> = ({ title, tags }) => (
  <div>
    <h5 className="text-sm font-bold text-slate-900 dark:text-white mb-2 pb-1 border-b border-slate-200 dark:border-slate-700">{title}</h5>
    <div className="space-y-1">
      <TagDetailLine label="Tytuł" value={tags.title} />
      <TagDetailLine label="Artysta" value={tags.artist} />
      <TagDetailLine label="Album" value={tags.album} />
      <TagDetailLine label="Rok" value={tags.year} />
      <TagDetailLine label="Gatunek" value={tags.genre} />
      <TagDetailLine label="Kompozytor" value={tags.composer} />
      <TagDetailLine label="Komentarz" value={tags.comments} />
    </div>
  </div>
);


const TagPreviewTooltip: React.FC<TagPreviewTooltipProps> = ({ originalTags, fetchedTags }) => {
  if (!fetchedTags) return null;

  return (
    <div className="absolute z-10 w-[44rem] max-w-3xl p-4 -mt-24 ml-16 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
      <div className="flex space-x-4">
        {/* Original Tags Column */}
        <div className="w-1/2">
          <TagColumn title="Oryginalne Tagi" tags={originalTags} />
        </div>
        
        <div className="w-px bg-slate-200 dark:bg-slate-700"></div>

        {/* Fetched Tags Column */}
        <div className="w-1/2">
          <h5 className="text-sm font-bold text-slate-900 dark:text-white mb-2 pb-1 border-b border-slate-200 dark:border-slate-700">Zaktualizowane Tagi</h5>
          <div className="flex space-x-3">
             <AlbumCover tags={fetchedTags} className="w-24 h-24 flex-shrink-0" />
             <div className="space-y-1 overflow-hidden flex-grow">
                <TagDetailLine label="Tytuł" value={fetchedTags.title} />
                <TagDetailLine label="Artysta" value={fetchedTags.artist} />
                 <TagDetailLine label="Art. albumu" value={fetchedTags.albumArtist} />
                <TagDetailLine label="Album" value={fetchedTags.album} />
                <TagDetailLine label="Rok" value={fetchedTags.year} />
                <TagDetailLine label="Gatunek" value={fetchedTags.genre} />
                <TagDetailLine label="Nr utworu" value={fetchedTags.trackNumber} />
                <TagDetailLine label="Nr dysku" value={fetchedTags.discNumber} />
             </div>
          </div>
           <div className="mt-2 space-y-1">
             <TagDetailLine label="Kompozytor" value={fetchedTags.composer} />
             <TagDetailLine label="Prawa aut." value={fetchedTags.copyright} />
             <TagDetailLine label="Komentarz" value={fetchedTags.comments} />
           </div>
        </div>
      </div>
    </div>
  );
};

export default TagPreviewTooltip;