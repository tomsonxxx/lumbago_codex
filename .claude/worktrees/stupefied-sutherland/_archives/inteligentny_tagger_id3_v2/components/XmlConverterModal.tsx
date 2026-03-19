import React, { useState, useCallback } from 'react';
import { parseRekordboxXml, parseVirtualDjXml, buildRekordboxXml, buildVirtualDjXml } from '../utils/xmlUtils';
import { GenericTrack } from '../types';

// Fix: Declare the global 'saveAs' function, which is expected to be provided by FileSaver.js
declare const saveAs: (blob: Blob, filename: string) => void;

interface XmlConverterModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ConversionStatus = 'idle' | 'parsing' | 'converting' | 'complete' | 'error';
type XmlFormat = 'rekordbox' | 'virtualdj' | 'unknown';

const XmlConverterModal: React.FC<XmlConverterModalProps> = ({ isOpen, onClose }) => {
  const [status, setStatus] = useState<ConversionStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [sourceFormat, setSourceFormat] = useState<XmlFormat>('unknown');
  const [targetFormat, setTargetFormat] = useState<XmlFormat>('unknown');
  const [convertedXmlString, setConvertedXmlString] = useState<string | null>(null);
  const [stats, setStats] = useState({ tracks: 0, cues: 0 });
  const [isDragActive, setIsDragActive] = useState(false);

  const resetState = () => {
    setStatus('idle');
    setError(null);
    setSourceFormat('unknown');
    setTargetFormat('unknown');
    setConvertedXmlString(null);
    setStats({ tracks: 0, cues: 0 });
  };

  const handleFile = useCallback(async (file: File) => {
    if (!file || !file.name.toLowerCase().endsWith('.xml')) {
        setError('Proszę upuścić prawidłowy plik XML.');
        return;
    }
    
    resetState();
    setStatus('parsing');

    try {
        const text = await file.text();
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(text, "application/xml");
        
        let parsedTracks: GenericTrack[];
        let originalXmlDoc: XMLDocument;

        if (xmlDoc.querySelector('DJ_PLAYLISTS')) {
            setSourceFormat('rekordbox');
            setTargetFormat('virtualdj');
            parsedTracks = parseRekordboxXml(xmlDoc);
            originalXmlDoc = parser.parseFromString('<VirtualDJ_Database Version="8.5"></VirtualDJ_Database>', "application/xml");
        } else if (xmlDoc.querySelector('VirtualDJ_Database')) {
            setSourceFormat('virtualdj');
            setTargetFormat('rekordbox');
            parsedTracks = parseVirtualDjXml(xmlDoc);
            originalXmlDoc = parser.parseFromString('<?xml version="1.0" encoding="UTF-8"?><DJ_PLAYLISTS Version="1.0.0"><PRODUCT Name="rekordbox" Version="6.5.3" Company="AlphaTheta, Inc."/><COLLECTION Entries="0"></COLLECTION></DJ_PLAYLISTS>', "application/xml");
        } else {
            throw new Error('Nie rozpoznano formatu pliku XML. Upewnij się, że jest to plik z Rekordbox lub VirtualDJ.');
        }

        setStatus('converting');

        const totalCues = parsedTracks.reduce((acc, track) => acc + track.cues.length, 0);
        setStats({ tracks: parsedTracks.length, cues: totalCues });

        let newXmlDoc;
        if (targetFormat === 'rekordbox') {
            newXmlDoc = buildRekordboxXml(parsedTracks, originalXmlDoc);
        } else {
            newXmlDoc = buildVirtualDjXml(parsedTracks, originalXmlDoc);
        }

        const serializer = new XMLSerializer();
        setConvertedXmlString(serializer.serializeToString(newXmlDoc));
        setStatus('complete');

    } catch (e) {
        setError(e instanceof Error ? e.message : 'Wystąpił nieznany błąd.');
        setStatus('error');
    }
  }, [targetFormat]);
  
  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleDrag = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setIsDragActive(true);
    else if (e.type === 'dragleave') setIsDragActive(false);
  }, []);
  
  const handleDownload = () => {
      if (!convertedXmlString) return;
      const blob = new Blob([convertedXmlString], { type: 'application/xml;charset=utf-8' });
      const filename = `converted_to_${targetFormat}.xml`;
      // Use FileSaver.js loaded globally
      saveAs(blob, filename);
  };
  
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50" onClick={onClose}>
      <div className="bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-2xl mx-4 transform transition-all duration-300 scale-95 opacity-0 animate-fade-in-scale" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-white mb-4">Konwerter XML</h2>
        <p className="text-sm text-slate-400 mb-4">
          Przeciągnij i upuść plik `database.xml` z VirtualDJ lub wyeksportowany XML z Rekordbox, aby przekonwertować go na format drugiej aplikacji, zachowując punkty CUE i inne metadane.
        </p>

        <div
          onDragEnter={handleDrag} onDragOver={handleDrag} onDragLeave={handleDrag} onDrop={handleDrop}
          className={`relative flex flex-col items-center justify-center w-full h-48 p-8 border-2 border-dashed rounded-lg transition-colors duration-300 ${isDragActive ? 'border-indigo-400 bg-slate-700' : 'border-slate-600'}`}
        >
          {status === 'idle' && (
             <div className="text-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-10 w-10 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                <p className="mt-2 text-slate-300">Przeciągnij plik XML tutaj</p>
            </div>
          )}
           {(status === 'parsing' || status === 'converting') && (
            <div className="text-center">
                <div className="btn-spinner !h-10 !w-10 !border-4 text-indigo-400"></div>
                <p className="mt-4 text-slate-300">{status === 'parsing' ? 'Analizuję plik...' : 'Konwertuję dane...'}</p>
            </div>
          )}
          {status === 'complete' && (
            <div className="text-center animate-fade-in">
                <h3 className="text-lg font-bold text-green-400">Konwersja zakończona!</h3>
                <p className="text-slate-300 mt-2">
                    Format źródłowy: <span className="font-semibold capitalize">{sourceFormat}</span>
                </p>
                <p className="text-slate-300">
                    Przekonwertowano <span className="font-semibold">{stats.tracks}</span> utworów i <span className="font-semibold">{stats.cues}</span> punktów CUE.
                </p>
            </div>
          )}
          {status === 'error' && (
            <div className="text-center animate-fade-in">
                <h3 className="text-lg font-bold text-red-400">Wystąpił błąd</h3>
                <p className="text-slate-300 mt-2 text-sm max-w-md">{error}</p>
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-4 mt-6 pt-4 border-t border-slate-700">
          {status !== 'complete' && status !== 'error' && <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700 rounded-md hover:bg-slate-600">Anuluj</button>}
          {(status === 'complete' || status === 'error') && <button onClick={resetState} className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700 rounded-md hover:bg-slate-600">Konwertuj inny</button>}
          {status === 'complete' && <button onClick={handleDownload} className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 rounded-md hover:bg-indigo-500">Pobierz plik</button>}
        </div>
        <style>{`.animate-fade-in-scale { animation: fade-in-scale 0.2s ease-out forwards; } @keyframes fade-in-scale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }`}</style>
      </div>
    </div>
  );
};

export default XmlConverterModal;