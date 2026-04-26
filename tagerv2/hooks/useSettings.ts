
import { useState, useEffect } from 'react';
import { ApiKeys, AIProvider } from '../services/aiService';
import { AnalysisSettings } from '../types';

const DEFAULT_ANALYSIS_SETTINGS: AnalysisSettings = {
  fields: {
    bpm: true,
    key: true,
    genre: true,
    year: true,
    label: true,
    energy: true,
    danceability: true,
    mood: true,
    isrc: false,
    album_artist: true,
    composer: false
  },
  mode: 'accurate'
};

export const useSettings = () => {
  // Theme
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (localStorage.getItem('theme') as 'light' | 'dark') || 'dark');
  
  // API keys are kept in memory only — never written to any browser storage
  // to avoid persisting credentials in cleartext.
  const [apiKeys, setApiKeys] = useState<ApiKeys>({ grok: '', openai: '' });

  // AI Provider
  const [aiProvider, setAiProvider] = useState<AIProvider>(() => (localStorage.getItem('aiProvider') as AIProvider) || 'gemini');

  // Rename Pattern
  const [renamePattern, setRenamePattern] = useState<string>(() => localStorage.getItem('renamePattern') || '[artist] - [title]');

  // Analysis Settings
  const [analysisSettings, setAnalysisSettings] = useState<AnalysisSettings>(() => {
    const saved = localStorage.getItem('analysisSettings');
    return saved ? { ...DEFAULT_ANALYSIS_SETTINGS, ...JSON.parse(saved) } : DEFAULT_ANALYSIS_SETTINGS;
  });

  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.documentElement.className = theme;
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('aiProvider', aiProvider);
    localStorage.setItem('renamePattern', renamePattern);
    localStorage.setItem('analysisSettings', JSON.stringify(analysisSettings));
  }, [aiProvider, renamePattern, analysisSettings]);

  return {
    theme,
    setTheme,
    apiKeys,
    setApiKeys,
    aiProvider,
    setAiProvider,
    renamePattern,
    setRenamePattern,
    analysisSettings,
    setAnalysisSettings
  };
};
