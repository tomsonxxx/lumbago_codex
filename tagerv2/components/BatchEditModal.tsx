import React, { useState, useMemo, useEffect } from "react";
import { AudioFile, ID3Tags } from "../types";

interface BatchEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (tagsToApply: Partial<ID3Tags>) => void;
  files: AudioFile[];
}

type EditableTags = Pick<
  ID3Tags,
  | "artist"
  | "albumArtist"
  | "album"
  | "year"
  | "genre"
  | "mood"
  | "comments"
  | "composer"
  | "copyright"
  | "encodedBy"
  | "originalArtist"
  | "discNumber"
>;
const editableTagKeys: (keyof EditableTags)[] = [
  "artist",
  "albumArtist",
  "album",
  "year",
  "genre",
  "composer",
  "originalArtist",
  "discNumber",
  "mood",
  "copyright",
  "encodedBy",
  "comments",
];

const BatchEditModal: React.FC<BatchEditModalProps> = ({
  isOpen,
  onClose,
  onSave,
  files,
}) => {
  const [tags, setTags] = useState<Partial<EditableTags>>({});
  const [fieldsToUpdate, setFieldsToUpdate] = useState<
    Record<keyof EditableTags, boolean>
  >(() =>
    editableTagKeys.reduce(
      (acc, key) => ({ ...acc, [key]: false }),
      {} as Record<keyof EditableTags, boolean>,
    ),
  );

  const commonTags = useMemo<Partial<EditableTags>>(() => {
    if (!files || files.length === 0) return {};
    const firstFileTags: Partial<ID3Tags> = files[0].fetchedTags || {};
    const result: Partial<EditableTags> = {};
    for (const key of editableTagKeys) {
      const firstValue = firstFileTags[key];
      if (
        files.every((f) => (f.fetchedTags?.[key] ?? "") === (firstValue ?? ""))
      ) {
        if (
          typeof firstValue === "string" ||
          typeof firstValue === "undefined"
        ) {
          result[key] = firstValue;
        }
      }
    }
    return result;
  }, [files]);

  useEffect(() => {
    if (isOpen) {
      setTags(commonTags);
      setFieldsToUpdate(
        editableTagKeys.reduce(
          (acc, key) => ({ ...acc, [key]: false }),
          {} as Record<keyof EditableTags, boolean>,
        ),
      );
    }
  }, [isOpen, commonTags]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    setTags((prev) => ({ ...prev, [name as keyof EditableTags]: value }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFieldsToUpdate((prev) => ({
      ...prev,
      [name as keyof EditableTags]: checked,
    }));
  };

  const handleSave = () => {
    const tagsToApply: Partial<ID3Tags> = {};
    for (const key of editableTagKeys) {
      if (fieldsToUpdate[key]) tagsToApply[key] = tags[key] || "";
    }
    onSave(tagsToApply);
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="glass-panel w-full max-w-2xl rounded-[2.5rem] p-8 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)] max-h-[90vh] overflow-y-auto scrollbar-hide"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
             <div className="p-3 bg-[var(--accent-cyan)] rounded-2xl glow-cyan">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
             </div>
             <div>
               <h2 className="text-2xl font-bold text-white font-heading">
                 Edycja Masowa
               </h2>
               <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest">Wybrano {files.length} utworów</p>
             </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-xl text-white/40 hover:text-white transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-6">
          <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
             <p className="text-xs text-white/40 leading-relaxed italic">Zaznacz pola, które chcesz zaktualizować we wszystkich wybranych plikach. Pola pozostawione be odznaczenia nie zostaną zmienione.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {editableTagKeys.map((key) => (
              <div key={key} className={`p-4 rounded-3xl border transition-all ${fieldsToUpdate[key] ? "bg-[var(--accent-cyan)]/5 border-[var(--accent-cyan)]/20 shadow-[0_0_15px_rgba(var(--accent-cyan-rgb),0.1)]" : "bg-white/5 border-white/5 opacity-60 hover:opacity-100"}`}>
                <div className="flex items-center gap-3 mb-3">
                  <input
                    type="checkbox"
                    id={`update-${key}`}
                    name={key}
                    checked={fieldsToUpdate[key]}
                    onChange={handleCheckboxChange}
                    className="h-5 w-5 rounded-lg border-white/20 bg-black/40 text-[var(--accent-cyan)] focus:ring-[var(--accent-cyan)]"
                  />
                  <label
                    htmlFor={`update-${key}`}
                    className={`text-[10px] uppercase font-bold tracking-widest cursor-pointer ${fieldsToUpdate[key] ? "text-[var(--accent-cyan)]" : "text-white/40"}`}
                  >
                    {key === "albumArtist" ? "Artist Album" : key === "originalArtist" ? "Orig. Artist" : key}
                  </label>
                </div>
                <input
                  type="text"
                  id={key}
                  name={key}
                  value={tags[key] || ""}
                  onChange={handleChange}
                  placeholder={commonTags[key] === undefined ? "(różne)" : ""}
                  className={`w-full bg-black/40 border rounded-xl py-2.5 px-4 text-xs text-white placeholder:text-white/10 transition-all focus:outline-none ${fieldsToUpdate[key] ? "border-[var(--accent-cyan)]/30 focus:border-[var(--accent-cyan)]" : "border-white/5 cursor-not-allowed"}`}
                  disabled={!fieldsToUpdate[key]}
                />
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-between items-center mt-10 pt-8 border-t border-white/5">
          <button
            onClick={onClose}
            className="px-6 py-3 text-xs font-bold text-white/30 hover:text-white transition-colors uppercase tracking-widest"
          >
            Anuluj
          </button>
          <button
            onClick={handleSave}
            className="px-10 py-4 bg-[var(--accent-magenta)] text-white text-xs font-bold rounded-2xl shadow-lg glow-magenta hover:scale-105 active:scale-95 transition-all uppercase tracking-widest"
          >
            Zastosuj zmiany
          </button>
        </div>
      </div>
    </div>
  );
};

export default BatchEditModal;
