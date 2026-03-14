
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Sidebar } from './components/Sidebar';
import { MainContent } from './components/MainContent';
import { Icons } from './Icons';

// Re-export features to ensure they are bundled correctly if index.tsx acts as an entry aggregator
export * from './features/ImportScanner';
export * from './features/LibraryBuilder';
export * from './features/DuplicateFinder';
export * from './features/Renamer';
export * from './features/PlayerWaveformViewer';
export * from './features/XMLConverter';
export * from './features/SmartTaggerAI';
export * from './features/AudioRecognizer';
export * from './features/PlaylistIntelligence';
export * from './features/CrateDigger';
export * from './features/SetRecorderAnalyzer';
export * from './features/CloudBackupSync';
export * from './features/MetadataAutoComplete';
export * from './features/WaveformColorCoding';
export * from './features/SmartCollections';
export * from './features/ExportManager';
export * from './features/LibraryBrowser';

const App = () => {
  const [activeFeature, setActiveFeature] = useState('libraryBrowser');

  return (
    <div className="flex bg-gray-900 min-h-screen">
      <Sidebar activeFeature={activeFeature} setActiveFeature={setActiveFeature} />
      <MainContent activeFeature={activeFeature} />
    </div>
  );
};

// Check if we are running in a browser environment before rendering
if (typeof document !== 'undefined') {
    const rootElement = document.getElementById('root');
    if (rootElement) {
        const root = createRoot(rootElement);
        root.render(<App />);
    }
}
