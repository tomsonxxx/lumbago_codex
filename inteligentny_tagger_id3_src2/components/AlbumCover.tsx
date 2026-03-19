import React from 'react';
import { ID3Tags } from '../types';
import { proxyImageUrl } from '../utils/audioUtils';

interface AlbumCoverProps {
  tags?: ID3Tags;
  className?: string;
}

const AlbumCover: React.FC<AlbumCoverProps> = ({ tags, className = "w-12 h-12" }) => {
  const coverUrl = proxyImageUrl(tags?.albumCoverUrl);

  return (
    <div className={`${className} rounded-md bg-slate-200 dark:bg-slate-700 flex items-center justify-center flex-shrink-0 shadow-md`}>
      {coverUrl ? (
        <img src={coverUrl} alt="Okładka albumu" className="w-full h-full object-cover rounded-md" crossOrigin="anonymous" />
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-slate-400 dark:text-slate-500" viewBox="0 0 20 20" fill="currentColor">
          <path d="M18 3a1 1 0 00-1.447-.894L4 6.424V20h12V6.424l2.553-1.318A1 1 0 0018 3zM4 4.382l10-3.138V4L4 7.138V4.382zM15 18H5V8.138l10-3.138V18z" />
          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
        </svg>
      )}
    </div>
  );
};

export default AlbumCover;