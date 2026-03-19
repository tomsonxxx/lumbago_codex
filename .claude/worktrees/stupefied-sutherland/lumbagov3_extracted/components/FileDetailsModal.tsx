import React, { useMemo } from 'react';
import { AudioFile, ID3Tags } from '../types';
import { analyzeFilename, formatFileSize, formatDate } from '../utils/metadataUtils';
import AlbumCover from './AlbumCover';

interface FileDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  file: AudioFile;
}

const FileDetailsModal: React.FC<FileDetailsModalProps> = ({ isOpen, onClose, file }) => {
  if (!isOpen) return null;

  const analysis = useMemo(() => analyzeFilename(file.file.name), [file.file.name]);
  const tags = file.fetchedTags || file.originalTags || {};

  // Helper do wyświetlania rzędu w tabeli
  const TagRow = ({ label, value, originalValue }: { label: string, value?: string | number, originalValue?: string | number }) => {
    const isDifferent = originalValue && value && originalValue !== value;
    
    if (!value && !originalValue) return null;

    return (
      <tr className="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50">
        <td className="py-2 px-3 text-sm font-medium text-slate-500 dark:text-slate-400">{label}</td>
        <td className="py-2 px-3 text-sm text-slate-800 dark:text-slate-200 font-mono break-all">
          {value || <span className="text-slate-400 italic">brak</span>}
          {isDifferent && (
            <div className="text-xs text-amber-600 dark:text-amber-500 mt-0.5">
               Oryg: {originalValue}
            </div>
          )}
        </td>
      </tr>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex justify-center items-center z-[60] p-4" onClick={onClose}>
      <div 
        className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col animate-fade-in-scale border border-slate-200 dark:border-slate-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
            <div className="flex items-center space-x-4 overflow-hidden">
                <div className="bg-indigo-100 dark:bg-indigo-900/30 p-2 rounded-lg text-indigo-600 dark:text-indigo-400">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <div className="min-w-0">
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white truncate">Inspektor Pliku</h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 truncate font-mono">{file.file.name}</p>
                </div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>

        {/* Content - Scrollable */}
        <div className="overflow-y-auto p-6 space-y-8 custom-scrollbar">
            
            {/* Sekcja 1: Podstawowe info i Analiza */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Karta pliku */}
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-5 border border-slate-200 dark:border-slate-700">
                     <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wide mb-4 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 011.414.586l5.414 5.414a1 1 0 01.586 1.414V19a2 2 0 01-2 2z" /></svg>
                        Dane Fizyczne
                     </h3>
                     <div className="space-y-3 text-sm">
                        <div className="flex justify-between">
                            <span className="text-slate-500 dark:text-slate-400">Rozmiar:</span>
                            <span className="font-mono text-slate-800 dark:text-slate-200">{formatFileSize(file.file.size)}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-500 dark:text-slate-400">Typ MIME:</span>
                            <span className="font-mono text-slate-800 dark:text-slate-200">{file.file.type || 'unknown'}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-500 dark:text-slate-400">Ostatnia modyfikacja:</span>
                            <span className="text-slate-800 dark:text-slate-200">{formatDate(file.file.lastModified)}</span>
                        </div>
                         <div className="flex justify-between">
                            <span className="text-slate-500 dark:text-slate-400">Ścieżka względna:</span>
                            <span className="font-mono text-slate-800 dark:text-slate-200 truncate max-w-[200px]" title={file.webkitRelativePath}>{file.webkitRelativePath || 'root'}</span>
                        </div>
                     </div>
                </div>

                {/* Inteligentna Analiza */}
                <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-5 border border-indigo-100 dark:border-indigo-900/50 relative overflow-hidden">
                     <div className="absolute top-0 right-0 p-2 opacity-10">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-24 w-24" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                     </div>
                     <h3 className="text-sm font-bold text-indigo-900 dark:text-indigo-200 uppercase tracking-wide mb-4 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                        Analiza Nazwy Pliku
                     </h3>
                     <div className="space-y-3 text-sm relative z-10">
                        <div className="flex justify-between">
                            <span className="text-indigo-700 dark:text-indigo-300 opacity-70">Wykryty wzorzec:</span>
                            <span className="font-bold text-indigo-900 dark:text-indigo-100">{analysis.pattern}</span>
                        </div>
                         <div className="flex justify-between items-center">
                            <span className="text-indigo-700 dark:text-indigo-300 opacity-70">Pewność:</span>
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                analysis.confidence === 'High' ? 'bg-green-100 text-green-700' :
                                analysis.confidence === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-red-100 text-red-700'
                            }`}>{analysis.confidence}</span>
                        </div>
                        <div className="pt-2 border-t border-indigo-200 dark:border-indigo-800/50">
                             {analysis.artist && <div className="flex justify-between"><span className="opacity-70">Artysta:</span> <span className="font-semibold">{analysis.artist}</span></div>}
                             {analysis.title && <div className="flex justify-between"><span className="opacity-70">Tytuł:</span> <span className="font-semibold">{analysis.title}</span></div>}
                             {analysis.trackNumber && <div className="flex justify-between"><span className="opacity-70">Nr utworu:</span> <span className="font-semibold">{analysis.trackNumber}</span></div>}
                        </div>
                     </div>
                </div>
            </div>

            {/* Sekcja 2: Metadane */}
            <div className="flex flex-col md:flex-row gap-8">
                {/* Okładka */}
                <div className="w-full md:w-1/3 flex flex-col items-center">
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wide mb-4 self-start">Okładka</h3>
                    <AlbumCover tags={tags} className="w-64 h-64 shadow-lg rounded-xl" />
                    <p className="mt-4 text-xs text-center text-slate-500 dark:text-slate-400">
                        {tags.albumCoverUrl ? 'Okładka osadzona lub z URL' : 'Brak okładki w metadanych'}
                    </p>
                </div>

                {/* Tabela Tagów */}
                <div className="w-full md:w-2/3">
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wide mb-4 flex items-center justify-between">
                        <span>Odczytane Tagi ID3</span>
                        <span className="text-xs font-normal text-slate-500 normal-case bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                           Stan: {file.fetchedTags ? 'Po edycji/AI' : 'Oryginalne'}
                        </span>
                    </h3>
                    <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden">
                        <table className="w-full">
                            <tbody>
                                <TagRow label="Tytuł" value={tags.title} originalValue={file.originalTags.title} />
                                <TagRow label="Artysta" value={tags.artist} originalValue={file.originalTags.artist} />
                                <TagRow label="Album" value={tags.album} originalValue={file.originalTags.album} />
                                <TagRow label="Wykonawca albumu" value={tags.albumArtist} originalValue={file.originalTags.albumArtist} />
                                <TagRow label="Rok" value={tags.year} originalValue={file.originalTags.year} />
                                <TagRow label="Gatunek" value={tags.genre} originalValue={file.originalTags.genre} />
                                <TagRow label="Nr utworu" value={tags.trackNumber} originalValue={file.originalTags.trackNumber} />
                                <TagRow label="Nr dysku" value={tags.discNumber} originalValue={file.originalTags.discNumber} />
                                <TagRow label="Kompozytor" value={tags.composer} originalValue={file.originalTags.composer} />
                                <TagRow label="Nastrój" value={tags.mood} originalValue={file.originalTags.mood} />
                                <TagRow label="Prawa autorskie" value={tags.copyright} originalValue={file.originalTags.copyright} />
                                <TagRow label="Oryginalny art." value={tags.originalArtist} originalValue={file.originalTags.originalArtist} />
                                <TagRow label="Bitrate" value={tags.bitrate ? `${tags.bitrate} kbps` : undefined} originalValue={file.originalTags.bitrate} />
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex justify-end">
            <button 
                onClick={onClose}
                className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow transition-colors"
            >
                Zamknij
            </button>
        </div>
      </div>
       <style>{`.animate-fade-in-scale { animation: fade-in-scale 0.2s ease-out forwards; } @keyframes fade-in-scale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }`}</style>
    </div>
  );
};

export default FileDetailsModal;