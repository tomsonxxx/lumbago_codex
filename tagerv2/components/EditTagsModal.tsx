import React, { useState, useEffect, useMemo } from "react";
import { AudioFile, ID3Tags } from "../types";
import AlbumCover from "./AlbumCover";
import { generateCoverArt } from "../services/aiService";

interface EditTagsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (tags: ID3Tags) => void;
  onApply: (tags: ID3Tags) => void;
  file: AudioFile;
  onManualSearch: (query: string, file: AudioFile) => Promise<void>;
  onZoomCover: (imageUrl: string) => void;
  isApplying: boolean;
  isDirectAccessMode: boolean;
  popularTags?: string[];
}

const EditTagsModal: React.FC<EditTagsModalProps> = ({
  isOpen,
  onClose,
  onSave,
  onApply,
  file,
  onManualSearch,
  onZoomCover,
  isApplying,
  isDirectAccessMode,
  popularTags = [],
}) => {
  const [tags, setTags] = useState<ID3Tags>({});
  const [manualQuery, setManualQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [, setSearchError] = useState<string | null>(null);

  // Image Generation State
  const [showGenPanel, setShowGenPanel] = useState(false);
  const [genPrompt, setGenPrompt] = useState("");
  const [genSize, setGenSize] = useState<"1K" | "2K">("1K");
  const [isGenerating, setIsGenerating] = useState(false);
  const [, setGenError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && file) {
      setTags(file.fetchedTags || file.originalTags || {});
      setManualQuery(file.file.name);
      setSearchError(null);

      // Pre-fill generation prompt
      const t = file.fetchedTags || file.originalTags;
      if (t) {
        setGenPrompt(
          `Album cover for ${t.genre || "Electronic"} music track titled "${t.title || ""}" by ${t.artist || ""}. High quality, abstract, artistic.`,
        );
      }
    }
  }, [isOpen, file]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const { name, value, type } = e.target;
    setTags((prevTags) => ({
      ...prevTags,
      [name]: type === "number" ? (value ? Number(value) : undefined) : value,
    }));
  };

  const handleSave = () => {
    onSave(tags);
  };

  const handleSearch = async () => {
    setIsSearching(true);
    setSearchError(null);
    try {
      await onManualSearch(manualQuery, file);
    } catch (error) {
      setSearchError(
        error instanceof Error
          ? error.message
          : "Wystąpił nieznany błąd wyszukiwania.",
      );
    } finally {
      setIsSearching(false);
    }
  };

  const handleGenerateImage = async () => {
    if (!genPrompt) return;
    setIsGenerating(true);
    setGenError(null);
    try {
      const imageUrl = await generateCoverArt(genPrompt, genSize);
      setTags((prev) => ({ ...prev, albumCoverUrl: imageUrl }));
      setShowGenPanel(false);
    } catch (error: any) {
      setGenError(error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    if (file) {
      setTags(file.fetchedTags || file.originalTags || {});
    }
  }, [file?.fetchedTags]);

  const initialTags = useMemo(
    () => file.fetchedTags || file.originalTags || {},
    [file.fetchedTags, file.originalTags],
  );
  const hasChanges = useMemo(
    () => JSON.stringify(tags) !== JSON.stringify(initialTags),
    [tags, initialTags],
  );

  if (!isOpen) return null;

  const tagFields: (keyof Omit<ID3Tags, "albumCoverUrl" | "comments">)[] = [
    "title",
    "artist",
    "albumArtist",
    "album",
    "year",
    "trackNumber",
    "discNumber",
    "genre",
    "composer",
    "originalArtist",
    "mood",
    "copyright",
    "encodedBy",
    "bitrate",
    "sampleRate",
  ];
  const tagLabels: Record<string, string> = {
    title: "Tytuł",
    artist: "Wykonawca",
    albumArtist: "Wykonawca albumu",
    album: "Album",
    year: "Rok",
    genre: "Gatunek",
    mood: "Nastrój",
    comments: "Komentarze",
    bitrate: "Bitrate (kbps)",
    sampleRate: "Sample Rate (Hz)",
    trackNumber: "Numer utworu",
    discNumber: "Numer dysku",
    composer: "Kompozytor",
    copyright: "Prawa autorskie",
    encodedBy: "Zakodowane przez",
    originalArtist: "Oryginalny wykonawca",
  };

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-md flex justify-center items-center z-50 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="glass-panel rounded-[2rem] p-8 w-full max-w-5xl mx-4 max-h-[90vh] overflow-y-auto scrollbar-hide border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-8">
           <div className="flex items-center gap-4">
              <div className="p-3 bg-[var(--accent-cyan)] rounded-2xl glow-cyan">
                 <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                 </svg>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white font-heading">Edytuj Tagi</h2>
                <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest truncate max-w-md">{file.file.name}</p>
              </div>
           </div>
           <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-xl text-white/40 hover:text-white transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
           </button>
        </div>

        {/* Manual Search */}
        <div className="mb-8 p-6 bg-white/5 rounded-3xl border border-white/5 space-y-4">
           <label className="text-[10px] uppercase tracking-widest text-white/30 font-bold">Wyszukaj Tagi (Ręcznie)</label>
           <div className="flex gap-3">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={manualQuery}
                  onChange={(e) => setManualQuery(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-2xl py-3 px-10 text-sm text-white focus:ring-2 focus:ring-[var(--accent-cyan)]/50 focus:outline-none"
                  placeholder="Np. Artist - Title..."
                />
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <button
                onClick={handleSearch}
                disabled={isSearching || !manualQuery}
                className="px-8 py-3 bg-white/10 hover:bg-white/20 text-white text-xs font-bold rounded-2xl transition-all disabled:opacity-30"
              >
                {isSearching ? "SZUKAM..." : "SZUKAJ"}
              </button>
           </div>
        </div>

        {/* Tags Form */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
           {/* Left: Artwork */}
           <div className="lg:col-span-4 space-y-6">
              <div className="relative group rounded-[2rem] overflow-hidden aspect-square shadow-2xl glass-effect border border-white/10">
                 <AlbumCover tags={tags} className="w-full h-full object-cover" />
                 <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-4">
                    <button onClick={() => tags.albumCoverUrl && onZoomCover(tags.albumCoverUrl)} className="p-3 bg-white/10 rounded-full text-white hover:bg-[var(--accent-cyan)] hover:text-black transition-all">
                       <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                         <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                       </svg>
                    </button>
                    <button onClick={() => setShowGenPanel(true)} className="px-4 py-2 bg-[var(--accent-magenta)] text-white text-[10px] font-bold rounded-full glow-magenta">
                       GENERUJ AI
                    </button>
                 </div>
              </div>

              {showGenPanel && (
                <div className="p-6 bg-[var(--accent-magenta)]/5 border border-[var(--accent-magenta)]/20 rounded-3xl space-y-4 animate-fade-in relative overflow-hidden">
                   <div className="absolute top-0 right-0 w-24 h-24 bg-[var(--accent-magenta)]/10 blur-2xl rounded-full -mr-12 -mt-12"></div>
                   <h4 className="text-[10px] font-bold text-[var(--accent-magenta)] uppercase tracking-widest">Generuj Okładkę (AI)</h4>
                   <textarea
                     value={genPrompt}
                     onChange={(e) => setGenPrompt(e.target.value)}
                     className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-xs text-white h-24 focus:outline-none"
                     placeholder="Opisz obraz..."
                   />
                   <div className="flex gap-2">
                      <select value={genSize} onChange={(e) => setGenSize(e.target.value as "1K" | "2K")} className="flex-1 bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-[10px] text-white">
                         <option value="1K">1024x1024</option>
                         <option value="2K">2048x2048</option>
                      </select>
                      <button onClick={handleGenerateImage} disabled={isGenerating} className="px-4 py-2 bg-[var(--accent-magenta)] text-white text-[10px] font-bold rounded-xl grow shadow-lg group">
                         {isGenerating ? "CZEKAJ..." : "STWÓRZ"}
                      </button>
                   </div>
                </div>
              )}

              <div className="space-y-2">
                 <label className="text-[10px] uppercase tracking-widest text-white/30 font-bold ml-1">URL OKŁADKI</label>
                 <input type="text" name="albumCoverUrl" value={tags.albumCoverUrl || ""} onChange={handleChange} className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-xs text-white/60 focus:text-white" />
              </div>
           </div>

           {/* Right: Fields */}
           <div className="lg:col-span-8">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                 {tagFields.map(key => (
                    <div key={key} className={["title", "album"].includes(key) ? "sm:col-span-2" : ""}>
                       <label className="text-[10px] uppercase tracking-widest text-white/30 font-bold ml-1 mb-2 block">{tagLabels[key]}</label>
                       <input
                         type={["year", "trackNumber", "bpm"].includes(key) ? "number" : "text"}
                         name={key}
                         value={tags[key] || ""}
                         onChange={handleChange}
                         className="w-full bg-white/5 border border-white/10 rounded-2xl py-3.5 px-5 text-sm text-white focus:border-[var(--accent-cyan)]/50 focus:ring-1 focus:ring-[var(--accent-cyan)]/20 transition-all font-medium"
                       />
                       {key === "genre" && popularTags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1.5 transition-all">
                            {popularTags.map(tag => (
                              <button
                                key={tag}
                                type="button"
                                onClick={() => setTags(prev => ({ ...prev, genre: tag }))}
                                className="px-2 py-1 bg-white/5 border border-white/5 rounded-md text-[9px] text-white/40 hover:text-white hover:bg-white/10 transition-all"
                              >
                                {tag}
                               </button>
                            ))}
                          </div>
                        )}
                    </div>
                 ))}
                 <div className="sm:col-span-2">
                    <label className="text-[10px] uppercase tracking-widest text-white/30 font-bold ml-1 mb-2 block">KOMENTARZE</label>
                    <textarea name="comments" value={tags.comments || ""} onChange={handleChange} rows={3} className="w-full bg-white/5 border border-white/10 rounded-2xl py-3.5 px-5 text-sm text-white h-24" />
                 </div>
              </div>
           </div>
        </div>

        {/* Footer actions */}
        <div className="mt-12 pt-8 border-t border-white/5 flex justify-between items-center">
           <button onClick={onClose} className="px-6 py-3 text-xs font-bold text-white/30 hover:text-white uppercase tracking-widest">ANULUJ</button>
           <div className="flex gap-4">
              <button 
                onClick={handleSave} 
                className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white text-xs font-bold rounded-2xl border border-white/10 uppercase tracking-widest transition-all"
              >
                ZAPISZ (CACHE)
              </button>
              {isDirectAccessMode && (
                <button 
                  onClick={() => onApply(tags)} 
                  disabled={isApplying || !hasChanges}
                  className="px-10 py-4 bg-[var(--accent-cyan)] text-black text-xs font-bold rounded-2xl glow-cyan uppercase tracking-widest hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:scale-100"
                >
                  {isApplying ? "ZAPISYWANIE..." : "ZASTOSUJ ZMIANY"}
                </button>
              )}
           </div>
        </div>
      </div>
    </div>
  );
};

export default EditTagsModal;
