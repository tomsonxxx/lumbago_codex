import React, { useState, useEffect } from "react";
import { AIProvider, ApiKeys } from "../services/aiService";
import { AnalysisSettings } from "../types";
import { GeminiIcon } from "./icons/GeminiIcon";
import { GrokIcon } from "./icons/GrokIcon";
import { OpenAIIcon } from "./icons/OpenAIIcon";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (
    keys: ApiKeys,
    provider: AIProvider,
    analysisSettings: AnalysisSettings,
  ) => void;
  currentKeys: ApiKeys;
  currentProvider: AIProvider;
  currentAnalysisSettings?: AnalysisSettings;
}

const providerOptions: {
  id: AIProvider;
  name: string;
  Icon: React.FC<React.SVGProps<SVGSVGElement>>;
}[] = [
  { id: "gemini", name: "Google Gemini", Icon: GeminiIcon },
  { id: "grok", name: "Grok", Icon: GrokIcon },
  { id: "openai", name: "OpenAI", Icon: OpenAIIcon },
];

const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onSave,
  currentKeys,
  currentProvider,
  currentAnalysisSettings,
}) => {
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [grokApiKey, setGrokApiKey] = useState("");
  const [openAIApiKey, setOpenAIApiKey] = useState("");
  const [provider, setProvider] = useState<AIProvider>(currentProvider);

  // Analysis Settings State
  const [analysisMode, setAnalysisMode] = useState<
    "fast" | "accurate" | "creative"
  >("accurate");
  const [analysisFields, setAnalysisFields] = useState<
    AnalysisSettings["fields"]
  >(
    currentAnalysisSettings?.fields || {
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
      composer: false,
    },
  );

  useEffect(() => {
    if (isOpen) {
      setGeminiApiKey(currentKeys.gemini || "");
      setGrokApiKey(currentKeys.grok || "");
      setOpenAIApiKey(currentKeys.openai || "");
      setProvider(currentProvider);
      if (currentAnalysisSettings) {
        setAnalysisMode(currentAnalysisSettings.mode);
        setAnalysisFields(currentAnalysisSettings.fields);
      }
    }
  }, [isOpen, currentKeys, currentProvider, currentAnalysisSettings]);

  const handleSave = () => {
    onSave(
      {
        gemini: geminiApiKey.trim(),
        grok: grokApiKey.trim(),
        openai: openAIApiKey.trim(),
      },
      provider,
      {
        mode: analysisMode,
        fields: analysisFields,
      },
    );
  };

  const toggleField = (key: keyof AnalysisSettings["fields"]) => {
    setAnalysisFields((prev) => ({ ...prev, [key]: !prev[key] }));
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
        className="glass-panel w-full max-w-2xl rounded-none p-6 text-left align-middle transition-all animate-fade-in-scale max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-[var(--text-secondary)] text-[var(--text-primary)]">
            Ustawienia
          </h2>
          <button
            onClick={onClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-secondary)]"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="space-y-8">
          {/* AI Provider Section */}
          <div>
            <h3 className="text-sm font-bold text-[var(--text-secondary)] text-[var(--text-primary)] uppercase tracking-wider mb-4 border-b border-[var(--border-color)] dark:border-[var(--border-color)] pb-2">
              Silnik AI
            </h3>
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
                    className={`flex items-center justify-center p-3 w-full text-sm font-medium text-center rounded-none cursor-pointer transition-all border ${
                      provider === id
                        ? "border-indigo-500 bg-[var(--accent-secondary)] dark:bg-[var(--accent-secondary)] text-[var(--accent-primary)] dark:text-[var(--accent-primary)] shadow-sm ring-1 ring-[var(--accent-primary)]"
                        : "border-[var(--border-color)] dark:border-[var(--border-color)] bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] text-[var(--text-secondary)] dark:text-[var(--text-secondary)] hover:bg-[var(--bg-panel)] dark:hover:bg-[var(--bg-panel)]"
                    }`}
                  >
                    <Icon className="w-5 h-5 mr-2" />
                    {name}
                  </label>
                </div>
              ))}
            </div>

            {/* API Keys */}
            <div className="space-y-3 p-4 bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] rounded-none border border-[var(--border-color)] dark:border-[var(--border-color)]">
              <div>
                <label
                  htmlFor="geminiApiKey"
                  className="block text-xs font-medium text-[var(--text-secondary)] dark:text-[var(--text-secondary)] mb-1"
                >
                  Klucz API Google Gemini
                </label>
                <input
                  type="password"
                  id="geminiApiKey"
                  value={geminiApiKey}
                  onChange={(e) => setGeminiApiKey(e.target.value)}
                  className="block w-full bg-[var(--bg-surface)] dark:bg-[var(--bg-panel)] border border-[var(--border-color)] dark:border-[var(--border-color)] rounded-none py-1.5 px-3 text-sm text-[var(--text-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                  placeholder="AIza..."
                />
                <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-500 hover:underline mt-1 inline-block">
                  Zdobądź klucz API Gemini (bezpłatny)
                </a>
              </div>
              <div>
                <label
                  htmlFor="grokApiKey"
                  className="block text-xs font-medium text-[var(--text-secondary)] dark:text-[var(--text-secondary)] mb-1"
                >
                  Klucz API Grok
                </label>
                <input
                  type="password"
                  id="grokApiKey"
                  value={grokApiKey}
                  onChange={(e) => setGrokApiKey(e.target.value)}
                  className="block w-full bg-[var(--bg-surface)] dark:bg-[var(--bg-panel)] border border-[var(--border-color)] dark:border-[var(--border-color)] rounded-none py-1.5 px-3 text-sm text-[var(--text-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                  placeholder="xai-..."
                />
              </div>
              <div>
                <label
                  htmlFor="openAIApiKey"
                  className="block text-xs font-medium text-[var(--text-secondary)] dark:text-[var(--text-secondary)] mb-1"
                >
                  Klucz API OpenAI
                </label>
                <input
                  type="password"
                  id="openAIApiKey"
                  value={openAIApiKey}
                  onChange={(e) => setOpenAIApiKey(e.target.value)}
                  className="block w-full bg-[var(--bg-surface)] dark:bg-[var(--bg-panel)] border border-[var(--border-color)] dark:border-[var(--border-color)] rounded-none py-1.5 px-3 text-sm text-[var(--text-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                  placeholder="sk-..."
                />
              </div>
              <p className="text-xs text-[var(--text-secondary)] italic mt-2">
                Klucze są przechowywane tylko w pamięci przeglądarki i nigdy nie opuszczają Twojego urządzenia.
              </p>
            </div>
          </div>

          {/* Analysis Configuration Section */}
          <div>
            <h3 className="text-sm font-bold text-[var(--text-secondary)] text-[var(--text-primary)] uppercase tracking-wider mb-4 border-b border-[var(--border-color)] dark:border-[var(--border-color)] pb-2">
              Konfiguracja Analizy
            </h3>

            <div className="mb-6">
              <label className="block text-sm font-medium text-[var(--text-secondary)] dark:text-[var(--text-secondary)] mb-2">
                Tryb Priorytetu
              </label>
              <div className="flex bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] p-1 rounded-none">
                {[
                  {
                    id: "fast",
                    label: "Szybkość (Flash)",
                    desc: "Mniej tokenów, szybciej",
                  },
                  {
                    id: "accurate",
                    label: "Dokładność (Pro)",
                    desc: "Sprawdza wiele źródeł",
                  },
                  {
                    id: "creative",
                    label: "Kreatywny",
                    desc: "Szersze interpretacje",
                  },
                ].map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setAnalysisMode(m.id as any)}
                    className={`flex-1 py-2 px-3 rounded-none text-sm font-medium transition-all ${
                      analysisMode === m.id
                        ? "bg-[var(--bg-surface)] dark:bg-[var(--bg-panel)] text-[var(--accent-primary)] dark:text-[var(--accent-primary)] shadow-sm"
                        : "text-[var(--text-secondary)] dark:text-[var(--text-secondary)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-secondary)]"
                    }`}
                    title={m.desc}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            <label className="block text-sm font-medium text-[var(--text-secondary)] dark:text-[var(--text-secondary)] mb-3">
              Analizowane Metadane
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { id: "bpm", label: "BPM (Tempo)" },
                { id: "key", label: "Tonacja (Camelot)" },
                { id: "genre", label: "Gatunek" },
                { id: "year", label: "Rok wydania" },
                { id: "label", label: "Wytwórnia (Label)" },
                { id: "album_artist", label: "Wykonawca Albumu" },
                { id: "composer", label: "Kompozytor" },
                { id: "energy", label: "Energia (1-10)" },
                { id: "danceability", label: "Taneczność" },
                { id: "mood", label: "Nastrój" },
                { id: "isrc", label: "Kod ISRC" },
              ].map((field) => (
                <label
                  key={field.id}
                  className="flex items-center space-x-3 p-2 rounded-none hover:bg-[var(--bg-panel)] dark:hover:bg-[var(--bg-panel)] cursor-pointer border border-transparent hover:border-[var(--border-color)] dark:hover:border-[var(--border-color)] transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={
                      analysisFields[
                        field.id as keyof AnalysisSettings["fields"]
                      ]
                    }
                    onChange={() =>
                      toggleField(field.id as keyof AnalysisSettings["fields"])
                    }
                    className="h-4 w-4 rounded text-[var(--accent-primary)] focus:ring-[var(--accent-primary)] border-[var(--border-color)] dark:border-[var(--border-color)] bg-[var(--bg-surface)] dark:bg-[var(--bg-panel)]"
                  />
                  <span className="text-sm text-[var(--text-secondary)] dark:text-[var(--text-secondary)]">
                    {field.label}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-4 mt-8 pt-4 border-t border-[var(--border-color)] dark:border-[var(--border-color)]">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] dark:text-[var(--text-secondary)] hover:bg-[var(--bg-panel)] dark:hover:bg-[var(--bg-panel)] rounded-none transition-colors"
          >
            Anuluj
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 text-sm font-bold text-white bg-[var(--accent-secondary)] rounded-none hover:bg-[var(--accent-secondary)] shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
          >
            Zapisz zmiany
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
