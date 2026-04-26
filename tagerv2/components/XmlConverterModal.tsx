import React, { useState, useRef } from "react";

interface XmlConverterModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ConvertedStats {
  tracks: number;
  playlists: number;
  cues: number;
}

const XmlConverterModal: React.FC<XmlConverterModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<
    "idle" | "parsing" | "converting" | "success" | "error"
  >("idle");
  const [stats, setStats] = useState<ConvertedStats | null>(null);
  const [convertedXml, setConvertedXml] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus("idle");
      setStats(null);
      setErrorMsg(null);
    }
  };

  const parseAndConvert = async () => {
    if (!file) return;
    setStatus("parsing");
    setErrorMsg(null);

    try {
      const text = await file.text();
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(text, "text/xml");
      const collection = xmlDoc.getElementsByTagName("COLLECTION")[0];
      const tracks = collection ? collection.getElementsByTagName("TRACK") : [];

      let cueCount = 0;
      Array.from(tracks).forEach((track: Element) => {
        cueCount += track.getElementsByTagName("POSITION_MARK").length;
      });

      setStats({
        tracks: tracks.length,
        playlists: xmlDoc.getElementsByTagName("NODE").length,
        cues: cueCount,
      });

      setStatus("converting");
      await new Promise((resolve) => setTimeout(resolve, 800));

      let vdjOutput = `<?xml version="1.0" encoding="UTF-8"?>\n<DJ_PLAYLISTS Version="1.0">\n<PRODUCT Name="VirtualDJ" Version="8.0" />\n<COLLECTION Entries="${tracks.length}">\n`;

      Array.from(tracks).forEach((track: Element) => {
        const title =
          track.getAttribute("Name")?.replace(/&/g, "&amp;") || "Unknown";
        const artist =
          track.getAttribute("Artist")?.replace(/&/g, "&amp;") || "Unknown";
        const path =
          track.getAttribute("Location")?.replace(/&/g, "&amp;") || "";
        const bpm = track.getAttribute("AverageBpm") || "0";
        const key = track.getAttribute("Tonality") || "";
        const totalTime = track.getAttribute("TotalTime") || "0";

        vdjOutput += ` <SONG FilePath="${path}" FileSize="0" Duration="${totalTime}">\n`;
        vdjOutput += `  <Tags Author="${artist}" Title="${title}" Bpm="${bpm}" Key="${key}" />\n`;

        const cues = track.getElementsByTagName("POSITION_MARK");
        Array.from(cues).forEach((cue: Element) => {
          const startSec = parseFloat(cue.getAttribute("Start") || "0");
          const startMs = Math.round(startSec * 1000);
          const name = cue.getAttribute("Name") || "Cue";
          const num = cue.getAttribute("Num") || "0";
          vdjOutput += `  <Poi Pos="${startMs}" Name="${name}" Type="cue" Num="${num}" />\n`;
        });
        vdjOutput += ` </SONG>\n`;
      });
      vdjOutput += `</COLLECTION>\n</DJ_PLAYLISTS>`;

      setConvertedXml(vdjOutput);
      setStatus("success");
    } catch (e: any) {
      console.error("XML Error", e);
      setStatus("error");
      setErrorMsg("Błąd parsowania XML.");
    }
  };

  const handleDownload = () => {
    if (!convertedXml || !file) return;
    const blob = new Blob([convertedXml], { type: "text/xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `VirtualDJ_${file.name}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="glass-panel w-full max-w-xl rounded-3xl p-8 border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.5)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[var(--accent-magenta)] rounded-xl glow-magenta">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
               </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white font-heading">Konwerter XML</h2>
              <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest">Rekordbox do VirtualDJ</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-lg text-white/40 hover:text-white transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-8">
          <div
            className={`border-2 border-dashed rounded-[2rem] p-12 text-center transition-all cursor-pointer group ${file ? "border-[var(--accent-cyan)] bg-[var(--accent-cyan)]/5" : "border-white/10 hover:border-white/20 hover:bg-white/5"}`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              accept=".xml"
              onChange={handleFileChange}
              className="hidden"
              ref={fileInputRef}
            />
            {file ? (
              <div className="space-y-2">
                <div className="p-4 bg-white/5 rounded-2xl inline-block mx-auto">
                   <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-[var(--accent-cyan)]" viewBox="0 0 20 20" fill="currentColor">
                     <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                   </svg>
                </div>
                <p className="text-lg font-bold text-white truncate max-w-xs mx-auto">
                  {file.name}
                </p>
                <p className="text-[10px] uppercase font-bold text-white/30 tracking-widest">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                   <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white/20 group-hover:text-white/60 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                   </svg>
                </div>
                <div>
                   <p className="text-sm font-bold text-white">Przeciągnij lub kliknij, aby wgrać XML</p>
                   <p className="text-[10px] text-white/30 uppercase tracking-widest font-bold mt-1">Obsługuje tylko format Rekordbox 6</p>
                </div>
              </div>
            )}
          </div>

          {status === "error" && errorMsg && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-500 rounded-2xl text-center text-sm font-bold">
              {errorMsg}
            </div>
          )}

          {status === "success" && stats && (
            <div className="bg-[var(--accent-cyan)]/5 border border-[var(--accent-cyan)]/20 rounded-[2rem] p-8 text-center animate-fade-in">
              <div className="w-12 h-12 bg-[var(--accent-cyan)] text-black rounded-full flex items-center justify-center mx-auto mb-4 glow-cyan">
                 <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
              </div>
              <p className="text-xl font-bold text-white mb-2">Gotowe!</p>
              <div className="flex justify-center gap-8 mb-6">
                 <div>
                    <p className="text-[10px] uppercase font-bold text-white/30 mb-1">Utwory</p>
                    <p className="text-lg font-bold text-white">{stats.tracks}</p>
                 </div>
                 <div>
                    <p className="text-[10px] uppercase font-bold text-white/30 mb-1">Cues</p>
                    <p className="text-lg font-bold text-white">{stats.cues}</p>
                 </div>
              </div>
              <button
                onClick={handleDownload}
                className="w-full py-4 bg-[var(--accent-cyan)] text-black font-bold rounded-2xl shadow-lg glow-cyan hover:scale-[1.02] active:scale-95 transition-all"
              >
                Pobierz XML dla VirtualDJ
              </button>
            </div>
          )}

          {status === "idle" && file && (
            <button
              onClick={parseAndConvert}
              className="w-full py-4 bg-[var(--accent-magenta)] text-white font-bold rounded-2xl shadow-lg glow-magenta hover:scale-[1.02] active:scale-95 transition-all"
            >
              KONWERTUJ
            </button>
          )}

          {(status === "parsing" || status === "converting") && (
            <div className="space-y-4 py-8">
               <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                 <div className="bg-[var(--accent-cyan)] h-full w-1/3 rounded-full animate-[loading_1s_infinite_linear] shadow-[0_0_10px_var(--accent-cyan)]"></div>
               </div>
               <p className="text-[10px] text-white/40 uppercase font-bold tracking-widest text-center animate-pulse">Przetwarzanie danych...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default XmlConverterModal;
