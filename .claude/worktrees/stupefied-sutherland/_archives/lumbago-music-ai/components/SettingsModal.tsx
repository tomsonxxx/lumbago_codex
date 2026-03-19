
import React, { useState, useEffect } from 'react';
import { AIProvider, ApiKeys } from '../services/aiService';
import { AnalysisSettings } from '../types';
import { GeminiIcon } from './icons/GeminiIcon';
import { GrokIcon } from './icons/GrokIcon';
import { OpenAIIcon } from './icons/OpenAIIcon';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (keys: ApiKeys, provider: AIProvider, analysisSettings: AnalysisSettings) => void;
  currentKeys: ApiKeys;
  currentProvider: AIProvider;
  currentAnalysisSettings?: AnalysisSettings;
}

const providerOptions: { id: AIProvider, name: string, Icon: React.FC<React.SVGProps<SVGSVGElement>> }[] = [
    { id: 'gemini', name: 'Google Gemini', Icon: GeminiIcon },
    { id: 'grok', name: 'Grok', Icon: GrokIcon },
    { id: 'openai', name: 'OpenAI', Icon: OpenAIIcon }
];

const SettingsModal: React.FC<SettingsModalProps> = ({ 
  isOpen, 
  onClose, 
  onSave, 
  currentKeys, 
  currentProvider,
  currentAnalysisSettings
}) => {
  const [grokApiKey, setGrokApiKey] = useState('');
  const [openAIApiKey, setOpenAIApiKey] = useState('');
  const [provider, setProvider] = useState<AIProvider>(currentProvider);
  
  // Analysis Settings State
  const [analysisMode, setAnalysisMode] = useState<'fast' | 'accurate' | 'creative'>('accurate');
  const [analysisFields, setAnalysisFields] = useState<AnalysisSettings['fields']>(currentAnalysisSettings?.fields || {
    bpm: true, key: true, genre: true, year: true, label: true, energy: true, danceability: true, mood: true, isrc: false, album_artist: true, composer: false
  });

  useEffect(() => {
    if (isOpen) {
      setGrokApiKey(currentKeys.grok || '');
      setOpenAIApiKey(currentKeys.openai || '');
      setProvider(currentProvider);
      if (currentAnalysisSettings) {
          setAnalysisMode(currentAnalysisSettings.mode);
          setAnalysisFields(currentAnalysisSettings.fields);
      }
    }
  }, [isOpen, currentKeys, currentProvider, currentAnalysisSettings]);

  const handleSave = () => {
    onSave({
      grok: grokApiKey.trim(),
      openai: openAIApiKey.trim(),
    }, provider, {
        mode: analysisMode,
        fields: analysisFields
    });
  };

  const toggleField = (key: keyof AnalysisSettings['fields']) => {
      setAnalysisFields(prev => ({ ...prev, [key]: !prev[key] }));
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
      onClick={onClose}
    >
      <div
        className="glass-panel w-full max-w-2xl rounded-2xl p-6 text-left align-middle transition-all animate-fade-in-scale max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Ustawienia</h2>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-500 dark:hover:text-slate-300">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
        </div>
        
        <div className="space-y-8">
            {/* AI Provider Section */}
            <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-4 border-b border-slate-200 dark:border-slate-700 pb-2">Silnik AI</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-4">
                    {providerOptions.map(({ id, name, Icon }) => (
                        <div key={id}>
                            <input
                                type="radio"
                                id={id}
                                name="aiProvider"
                                value={id}
                                checked={provider === id}
                                onChange={() => setProvider(id)}
                                className="sr-only peer"
                            />
                            <label
                                htmlFor={id}
                                className={`flex items-center justify-center p-3 w-full text-sm font-medium text-center rounded-lg cursor-pointer transition-all border ${
                                    provider === id
                                    ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 shadow-sm ring-1 ring-indigo-500'
                                    : 'border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/30 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                                }`}
                            >
                                <Icon className="w-5 h-5 mr-2" />
                                {name}
                            </label>
                        </div>
                    ))}
                </div>
                
                {/* API Keys */}
                <div className="space-y-3 p-4 bg-slate-50 dark:bg-slate-900/30 rounded-lg border border-slate-200 dark:border-slate-800">
                    <div>
                        <label htmlFor="grokApiKey" className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Klucz API Grok</label>
                        <input
                        type="password"
                        id="grokApiKey"
                        value={grokApiKey}
                        onChange={(e) => setGrokApiKey(e.target.value)}
                        className="block w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-md py-1.5 px-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="xai-..."
                        />
                    </div>
                    <div>
                        <label htmlFor="openAIApiKey" className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">Klucz API OpenAI</label>
                        <input
                        type="password"
                        id="openAIApiKey"
                        value={openAIApiKey}
                        onChange={(e) => setOpenAIApiKey(e.target.value)}
                        className="block w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-md py-1.5 px-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="sk-..."
                        />
                    </div>
                    <p className="text-xs text-slate-400 italic mt-2">* Gemini używa wbudowanego klucza systemowego, chyba że podasz własny w zmiennych środowiskowych.</p>
                </div>
            </div>

            {/* Analysis Configuration Section */}
            <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-4 border-b border-slate-200 dark:border-slate-700 pb-2">Konfiguracja Analizy</h3>
                
                <div className="mb-6">
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Tryb Priorytetu</label>
                    <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                        {[
                            { id: 'fast', label: 'Szybkość (Flash)', desc: 'Mniej tokenów, szybciej' },
                            { id: 'accurate', label: 'Dokładność (Pro)', desc: 'Sprawdza wiele źródeł' },
                            { id: 'creative', label: 'Kreatywny', desc: 'Szersze interpretacje' }
                        ].map(m => (
                            <button
                                key={m.id}
                                onClick={() => setAnalysisMode(m.id as any)}
                                className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all ${
                                    analysisMode === m.id 
                                    ? 'bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-300 shadow-sm' 
                                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                                }`}
                                title={m.desc}
                            >
                                {m.label}
                            </button>
                        ))}
                    </div>
                </div>

                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">Analizowane Metadane</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {[
                        { id: 'bpm', label: 'BPM (Tempo)' },
                        { id: 'key', label: 'Tonacja (Camelot)' },
                        { id: 'genre', label: 'Gatunek' },
                        { id: 'year', label: 'Rok wydania' },
                        { id: 'label', label: 'Wytwórnia (Label)' },
                        { id: 'album_artist', label: 'Wykonawca Albumu' },
                        { id: 'composer', label: 'Kompozytor' },
                        { id: 'energy', label: 'Energia (1-10)' },
                        { id: 'danceability', label: 'Taneczność' },
                        { id: 'mood', label: 'Nastrój' },
                        { id: 'isrc', label: 'Kod ISRC' },
                    ].map(field => (
                        <label key={field.id} className="flex items-center space-x-3 p-2 rounded-md hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer border border-transparent hover:border-slate-200 dark:hover:border-slate-700 transition-colors">
                            <input
                                type="checkbox"
                                checked={analysisFields[field.id as keyof AnalysisSettings['fields']]}
                                onChange={() => toggleField(field.id as keyof AnalysisSettings['fields'])}
                                className="h-4 w-4 rounded text-indigo-600 focus:ring-indigo-500 border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700"
                            />
                            <span className="text-sm text-slate-700 dark:text-slate-300">{field.label}</span>
                        </label>
                    ))}
                </div>
            </div>
        </div>

        <div className="flex justify-end space-x-4 mt-8 pt-4 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/50 rounded-lg transition-colors"
          >
            Anuluj
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 text-sm font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
          >
            Zapisz zmiany
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
