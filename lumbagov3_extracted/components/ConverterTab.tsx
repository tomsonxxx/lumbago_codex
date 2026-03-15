import React, { useState } from 'react';
import { detectAndParseXML, ParsedLibrary } from '../utils/xmlParser';

const ConverterTab: React.FC = () => {
  const [parsedData, setParsedData] = useState<ParsedLibrary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setError(null);
    setParsedData(null);

    try {
      const data = await detectAndParseXML(file);
      setParsedData(data);
    } catch (err: any) {
      setError(err.message || "Wystąpił błąd podczas parsowania.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="animate-fade-in p-4 pb-20 max-w-4xl mx-auto">
      <div className="bg-slate-100 dark:bg-slate-800/50 p-8 rounded-xl border border-slate-200 dark:border-slate-700 text-center mb-8">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">Konwerter Biblioteki</h2>
        <p className="text-slate-500 dark:text-slate-400 mb-6">
          Zaimportuj plik XML z Rekordbox lub VirtualDJ, aby przeanalizować swoją bibliotekę i przygotować migrację.
        </p>
        
        <label className="inline-flex items-center px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg shadow-lg cursor-pointer transition-transform transform hover:scale-105">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span>Wybierz plik XML</span>
            <input type="file" accept=".xml" onChange={handleFileUpload} className="hidden" disabled={isProcessing} />
        </label>
        
        {isProcessing && <p className="mt-4 text-indigo-500 animate-pulse">Analizowanie pliku...</p>}
        {error && <p className="mt-4 text-red-500 font-medium">Błąd: {error}</p>}
      </div>

      {parsedData && (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                    <h3 className="text-xs text-slate-500 uppercase font-bold">Program</h3>
                    <p className="text-xl font-bold text-indigo-600 dark:text-indigo-400">{parsedData.program}</p>
                </div>
                <div className="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                    <h3 className="text-xs text-slate-500 uppercase font-bold">Liczba utworów</h3>
                    <p className="text-xl font-bold text-slate-800 dark:text-white">{parsedData.tracks.length}</p>
                </div>
                <div className="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                    <h3 className="text-xs text-slate-500 uppercase font-bold">Liczba playlist</h3>
                    <p className="text-xl font-bold text-slate-800 dark:text-white">{parsedData.playlists.length}</p>
                </div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
                <div className="p-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-700/30">
                    <h3 className="font-bold text-slate-800 dark:text-white">Znalezione Playlisty</h3>
                </div>
                <div className="max-h-64 overflow-y-auto">
                    {parsedData.playlists.length === 0 ? (
                        <p className="p-4 text-slate-500 italic">Brak playlist w pliku.</p>
                    ) : (
                        <ul className="divide-y divide-slate-100 dark:divide-slate-700">
                            {parsedData.playlists.map((pl, idx) => (
                                <li key={idx} className="p-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 flex justify-between items-center">
                                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{pl.Name}</span>
                                    <span className="text-xs bg-slate-200 dark:bg-slate-600 text-slate-600 dark:text-slate-300 px-2 py-1 rounded-full">
                                        {pl.Tracks.length} utw.
                                    </span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
            
            <div className="flex justify-end">
                 <button className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors" onClick={() => {
                     const json = JSON.stringify(parsedData, null, 2);
                     const blob = new Blob([json], {type: 'application/json'});
                     const url = URL.createObjectURL(blob);
                     const a = document.createElement('a');
                     a.href = url;
                     a.download = `converted_${parsedData.program.toLowerCase()}.json`;
                     a.click();
                 }}>
                     Eksportuj do JSON
                 </button>
            </div>
        </div>
      )}
    </div>
  );
};

export default ConverterTab;