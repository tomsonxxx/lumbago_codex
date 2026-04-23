import React, { useState, useEffect, useRef, useMemo } from "react";
import { AudioFile, ID3Tags } from "../types";
import { generatePath } from "../utils/filenameUtils";

interface RenameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (newPattern: string) => void;
  currentPattern: string;
  files: AudioFile[];
}

const placeholders: (keyof Omit<
  ID3Tags,
  "albumCoverUrl" | "comments" | "mood" | "bitrate" | "sampleRate"
>)[] = [
  "title",
  "artist",
  "albumArtist",
  "album",
  "trackNumber",
  "year",
  "genre",
  "composer",
  "originalArtist",
];

const RenameModal: React.FC<RenameModalProps> = ({
  isOpen,
  onClose,
  onSave,
  currentPattern,
  files,
}) => {
  const [pattern, setPattern] = useState(currentPattern);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setPattern(currentPattern);
    }
  }, [isOpen, currentPattern]);

  const insertPlaceholder = (placeholder: string) => {
    const text = `[${placeholder}]`;
    const input = inputRef.current;
    if (!input) return;
    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const newPattern =
      pattern.substring(0, start) + text + pattern.substring(end);
    setPattern(newPattern);
    setTimeout(() => {
      input.focus();
      input.setSelectionRange(start + text.length, start + text.length);
    }, 0);
  };

  const previews = useMemo(() => {
    if (!files || files.length === 0) return [];
    return files.slice(0, 5).map((file) => {
      const previewName = generatePath(
        pattern,
        file.fetchedTags || file.originalTags,
        file.file.name,
      );
      return { originalName: file.file.name, newName: previewName };
    });
  }, [pattern, files]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="glass-panel w-full max-w-2xl rounded-none p-6 animate-fade-in-scale"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-[var(--text-secondary)] text-[var(--text-primary)]">
            Zmiana nazw plików
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

        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] dark:text-[var(--text-secondary)] mb-2">
            Szablon nazwy
          </label>
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={pattern}
              onChange={(e) => setPattern(e.target.value)}
              className="block w-full bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] border border-[var(--border-color)] dark:border-[var(--border-color)] rounded-none py-2 px-4 text-[var(--text-secondary)] text-[var(--text-primary)] font-mono text-sm focus:ring-2 focus:ring-[var(--accent-primary)] focus:outline-none transition-shadow"
            />
          </div>
        </div>

        <div className="mt-4">
          <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2">
            Dostępne tagi
          </p>
          <div className="flex flex-wrap gap-2">
            {placeholders.map((p) => (
              <button
                key={p}
                onClick={() => insertPlaceholder(p)}
                className="px-2 py-1 text-xs font-mono bg-[var(--accent-secondary)] dark:bg-[var(--accent-secondary)] text-[var(--accent-primary)] dark:text-[var(--accent-primary)] border border-indigo-100 dark:border-indigo-800 rounded hover:bg-[var(--accent-secondary)] dark:hover:bg-[var(--accent-secondary)] transition-colors"
              >
                [{p}]
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] rounded-none p-4 border border-[var(--border-color)] dark:border-[var(--border-color)]">
          <p className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-3">
            Podgląd (5 pierwszych)
          </p>
          <div className="space-y-2">
            {previews.map((preview, idx) => (
              <div key={idx} className="flex items-center text-xs font-mono">
                <span className="text-[var(--text-secondary)] truncate w-1/2 text-right pr-2">
                  {preview.originalName}
                </span>
                <svg
                  className="w-3 h-3 text-[var(--text-secondary)] mx-2 flex-shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
                <span className="text-[var(--accent-primary)] dark:text-[var(--accent-primary)] truncate w-1/2 font-bold">
                  {preview.newName}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-[var(--border-color)] dark:border-[var(--border-color)]">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] dark:text-[var(--text-secondary)] hover:bg-[var(--bg-panel)] dark:hover:bg-[var(--bg-panel)] rounded-none transition-colors"
          >
            Anuluj
          </button>
          <button
            onClick={() => onSave(pattern)}
            className="px-6 py-2 text-sm font-bold text-white bg-[var(--accent-secondary)] rounded-none hover:bg-[var(--accent-secondary)] shadow-md transition-all active:scale-95"
          >
            Zapisz Schemat
          </button>
        </div>
      </div>
    </div>
  );
};

export default RenameModal;
