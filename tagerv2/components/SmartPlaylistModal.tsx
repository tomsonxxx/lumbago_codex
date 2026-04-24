import React, { useState } from "react";
import { AudioFile } from "../types";
import { generateSmartPlaylist } from "../services/aiService";

interface SmartPlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  files: AudioFile[];
  onCreatePlaylist: (name: string, ids: string[]) => void;
}

const SmartPlaylistModal: React.FC<SmartPlaylistModalProps> = ({
  isOpen,
  onClose,
  files,
  onCreatePlaylist,
}) => {
  const [prompt, setPrompt] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    if (files.length === 0) {
      setError(
        "Biblioteka jest pusta. Dodaj utwory, aby wygenerować playlistę.",
      );
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const result = await generateSmartPlaylist(files, prompt);

      if (result.ids.length === 0) {
        setError(
          "AI nie znalazło żadnych utworów pasujących do Twojego opisu.",
        );
      } else {
        onCreatePlaylist(result.name, result.ids);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || "Wystąpił błąd podczas komunikacji z AI.");
    } finally {
      setIsProcessing(false);
    }
  };

  const suggestions = [
    "Szybki trening cardio (130+ BPM)",
    "Deep House na zachód słońca",
    "Klasyki z lat 90",
    "Mroczne techno do podziemnego klubu",
    "Spokojny jazz do pracy",
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="glass-panel w-full max-w-lg rounded-none p-6 animate-fade-in-scale"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-none bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mr-3 shadow-lg shadow-indigo-500/30">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-white"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8 6.5 10.866a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-[var(--text-secondary)] text-[var(--text-primary)]">
              Smart Playlist AI
            </h2>
          </div>
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

        <div className="space-y-4">
          <p className="text-sm text-[var(--text-secondary)] dark:text-[var(--text-secondary)]">
            Opisz klimat, okazję lub rodzaj muzyki, a AI stworzy dla Ciebie
            idealną playlistę, analizując BPM, tonację i energię utworów w
            Twojej bibliotece.
          </p>

          <div>
            <label className="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
              Twój Opis
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Np. Energetyczny set na siłownię z dużą ilością basu..."
              className="w-full h-32 p-3 bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] border border-[var(--border-color)] dark:border-[var(--border-color)] rounded-none focus:ring-2 focus:ring-[var(--accent-primary)] focus:outline-none text-[var(--text-secondary)] text-[var(--text-primary)] resize-none shadow-inner"
              disabled={isProcessing}
            />
          </div>

          {!isProcessing && !prompt && (
            <div className="flex flex-wrap gap-2 mt-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => setPrompt(s)}
                  className="text-xs px-2 py-1 bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] text-[var(--text-secondary)] hover:bg-[var(--accent-secondary)] dark:hover:bg-[var(--accent-secondary)] hover:text-[var(--accent-primary)] dark:hover:text-[var(--accent-primary)] rounded-none transition-colors border border-transparent hover:border-indigo-200 dark:hover:border-indigo-800"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-300 rounded-none text-sm flex items-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 mr-2 flex-shrink-0"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              {error}
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={isProcessing || !prompt.trim()}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-none shadow-lg shadow-indigo-500/20 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isProcessing ? (
              <>
                <span className="btn-spinner mr-2"></span>
                Analizuję bibliotekę...
              </>
            ) : (
              <>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 mr-2"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                    clipRule="evenodd"
                  />
                </svg>
                Generuj Playlistę
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SmartPlaylistModal;
