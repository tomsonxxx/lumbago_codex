
import React, { useState, useEffect } from 'react';
import { AudioFile, ID3Tags } from '../types';
import { findDuplicates, DuplicateGroup } from '../utils/duplicateUtils';
import AlbumCover from './AlbumCover';
import { StatusIcon } from './StatusIcon';

interface DuplicateFinderTabProps {
  files: AudioFile[];
  onDelete: (fileId: string) => void;
  onPlayPause: (fileId: string) => void;
  playingFileId: string | null;
  isPlaying: boolean;
}

const DuplicateFinderTab: React.FC<DuplicateFinderTabProps> = ({ 
  files, 
  onDelete, 
  onPlayPause, 
  playingFileId, 
  isPlaying 
}) => {
  const [groups, setGroups] = useState<DuplicateGroup[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [scannedOnce, setScannedOnce] = useState(false);

  const handleScan = () => {
    setIsScanning(true);
    // Symulacja asynchroniczności, żeby UI nie zamarzł przy dużej liczbie plików
    setTimeout(() => {
      const results = findDuplicates(files);
      setGroups(results);
      setIsScanning(false);
      setScannedOnce(true);
    }, 100);
  };

  const keepBest = (groupId: string, criteria: 'bitrate' | 'newest' | 'oldest') => {
    const group = groups.find(g => g.id === groupId);
    if (!group) return;

    let fileToKeep: AudioFile | null = null;

    if (criteria === 'bitrate') {
      // Szukamy najwyższego bitrate
      fileToKeep = group.files.reduce((prev, current) => {
        const prevBitrate = prev.fetchedTags?.bitrate || prev.originalTags.bitrate || 0;
        const currBitrate = current.fetchedTags?.bitrate || current.originalTags.bitrate || 0;
        return (prevBitrate > currBitrate) ? prev : current;
      });
    } else if (criteria === 'newest') {
       // Najnowszy plik (data modyfikacji)
       fileToKeep = group.files.reduce((prev, current) => (prev.file.lastModified > current.file.lastModified ? prev : current));
    } else {
       // Najstarszy plik
       fileToKeep = group.files.reduce((prev, current) => (prev.file.lastModified < current.file.lastModified ? prev : current));
    }

    if (fileToKeep) {
       // Usuwamy wszystkie POZA fileToKeep
       group.files.forEach(f => {
           if (f.id !== fileToKeep!.id) {
               onDelete(f.id);
           }
       });
       // Aktualizuj lokalny stan usuwając grupę
       setGroups(prev => prev.filter(g => g.id !== groupId));
    }
  };
  
  // Usuń grupę z widoku (ignoruj duplikat)
  const ignoreGroup = (groupId: string) => {
      setGroups(prev => prev.filter(g => g.id !== groupId));
  }

  return (
    <div className="animate-fade-in p-4 pb-20">
      <div className="text-center mb-8 bg-slate-100 dark:bg-slate-800/50 p-6 rounded-xl border border-slate-200 dark:border-slate-700">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Wyszukiwarka Duplikatów</h2>
        <p className="text-slate-500 dark:text-slate-400 mb-6">
          Znajdź i usuń powtarzające się utwory, aby zaoszczędzić miejsce i uporządkować bibliotekę.
        </p>
        <button
          onClick={handleScan}
          disabled={isScanning}
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg shadow-lg transition-transform transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center mx-auto"
        >
          {isScanning ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Skanowanie...
              </>
          ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                {scannedOnce ? 'Skanuj ponownie' : 'Rozpocznij skanowanie'}
              </>
          )}
        </button>
      </div>

      {scannedOnce && groups.length === 0 && (
          <div className="text-center text-green-600 dark:text-green-400 p-8">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <p className="text-xl font-semibold">Świetnie! Nie znaleziono duplikatów.</p>
          </div>
      )}

      <div className="space-y-6">
        {groups.map((group) => (
          <div key={group.id} className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            <div className="bg-slate-50 dark:bg-slate-700/50 p-3 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
              <div>
                 <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 bg-slate-200 dark:bg-slate-600 px-2 py-0.5 rounded mr-2">
                    {group.type === 'filename' ? 'Nazwa pliku' : group.type === 'metadata' ? 'Tagi' : 'Rozmiar'}
                 </span>
                 <span className="font-medium text-slate-800 dark:text-slate-200">{group.key}</span>
              </div>
              <div className="flex space-x-2">
                  <button onClick={() => keepBest(group.id, 'bitrate')} className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors">
                      Zachowaj najlepszą jakość
                  </button>
                  <button onClick={() => ignoreGroup(group.id)} className="text-xs px-2 py-1 bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors">
                      Ignoruj
                  </button>
              </div>
            </div>
            
            <div className="divide-y divide-slate-100 dark:divide-slate-700">
               {group.files.map(file => {
                   const tags = file.fetchedTags || file.originalTags;
                   const bitrate = tags.bitrate || 0;
                   const isPlayingThis = playingFileId === file.id && isPlaying;

                   return (
                       <div key={file.id} className="p-3 flex items-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                           <div className="relative mr-4 group cursor-pointer" onClick={() => onPlayPause(file.id)}>
                               <AlbumCover tags={tags} className="w-10 h-10" />
                               <div className={`absolute inset-0 flex items-center justify-center bg-black/40 rounded-md transition-opacity ${isPlayingThis ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                                    {isPlayingThis ? (
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                                    ) : (
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white pl-0.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" /></svg>
                                    )}
                               </div>
                           </div>
                           
                           <div className="flex-grow min-w-0">
                               <div className="flex items-center">
                                   <p className="text-sm font-medium text-slate-900 dark:text-white truncate" title={file.file.name}>{file.file.name}</p>
                                   <StatusIcon state={file.state} />
                               </div>
                               <div className="flex text-xs text-slate-500 dark:text-slate-400 space-x-3 mt-0.5">
                                   <span>{(file.file.size / 1024 / 1024).toFixed(2)} MB</span>
                                   <span>•</span>
                                   <span className={bitrate > 300 ? 'text-green-600 dark:text-green-400 font-bold' : ''}>{bitrate ? `${bitrate} kbps` : 'N/A'}</span>
                                   <span>•</span>
                                   <span>{file.webkitRelativePath || 'root'}</span>
                               </div>
                           </div>

                           <button 
                                onClick={() => onDelete(file.id)}
                                className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-colors"
                                title="Usuń ten plik"
                           >
                               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                           </button>
                       </div>
                   )
               })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DuplicateFinderTab;
