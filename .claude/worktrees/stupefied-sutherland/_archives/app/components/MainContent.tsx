
import React from 'react';
import { ImportScanner } from '../features/ImportScanner';
import { LibraryBuilder } from '../features/LibraryBuilder';
import { DuplicateFinder } from '../features/DuplicateFinder';
import { Renamer } from '../features/Renamer';
import { PlayerWaveformViewer } from '../features/PlayerWaveformViewer';
import { XMLConverter } from '../features/XMLConverter';
import { SmartTaggerAI } from '../features/SmartTaggerAI';
import { AudioRecognizer } from '../features/AudioRecognizer';
import { PlaylistIntelligence } from '../features/PlaylistIntelligence';
import { CrateDigger } from '../features/CrateDigger';
import { SetRecorderAnalyzer } from '../features/SetRecorderAnalyzer';
import { CloudBackupSync } from '../features/CloudBackupSync';
import { MetadataAutoComplete } from '../features/MetadataAutoComplete';
import { WaveformColorCoding } from '../features/WaveformColorCoding';
import { SmartCollections } from '../features/SmartCollections';
import { ExportManager } from '../features/ExportManager';
import { LibraryBrowser } from '../features/LibraryBrowser';

export const MainContent = ({ activeFeature }: { activeFeature: string }) => {
  const renderContent = () => {
    switch (activeFeature) {
      case 'libraryBrowser': return <LibraryBrowser />;
      case 'scanner': return <ImportScanner />;
      case 'library': return <LibraryBuilder />;
      case 'duplicates': return <DuplicateFinder />;
      case 'renamer': return <Renamer />;
      case 'player': return <PlayerWaveformViewer />;
      case 'tagger': return <SmartTaggerAI />;
      case 'recognizer': return <AudioRecognizer />;
      case 'converter': return <XMLConverter />;
      case 'playlist': return <PlaylistIntelligence />;
      case 'cratedigger': return <CrateDigger />;
      case 'recorder': return <SetRecorderAnalyzer />;
      case 'cloud': return <CloudBackupSync />;
      case 'metadata': return <MetadataAutoComplete />;
      case 'waveform': return <WaveformColorCoding />;
      case 'collections': return <SmartCollections />;
      case 'export': return <ExportManager />;
      default: return <LibraryBrowser />;
    }
  };

  return (
    <main className="ml-64 p-8 min-h-screen bg-gray-900 text-gray-100">
      <header className="mb-8 flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-100 capitalize">
          {activeFeature.replace(/([A-Z])/g, ' $1').trim()} Module
        </h2>
      </header>
      <div className="max-w-7xl mx-auto h-[calc(100vh-140px)]">
        {renderContent()}
      </div>
    </main>
  );
};
