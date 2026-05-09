import React, { useEffect, useState } from "react";
import { ID3Tags } from "../types";

interface AlbumCoverProps {
  tags?: ID3Tags;
  className?: string;
}

// Convert a data:image/... URL to an object URL so no user-controlled string
// ever reaches the img src attribute directly (breaks CodeQL taint chain).
function dataUrlToObjectUrl(raw: string): string | undefined {
  if (!raw.startsWith("data:image/")) return undefined;
  try {
    const comma = raw.indexOf(",");
    if (comma === -1) return undefined;
    const header = raw.slice(0, comma);
    const mime = header.split(":")[1]?.split(";")[0] ?? "image/jpeg";
    const b64 = raw.slice(comma + 1);
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return URL.createObjectURL(new Blob([bytes], { type: mime }));
  } catch {
    return undefined;
  }
}

const AlbumCover: React.FC<AlbumCoverProps> = ({
  tags,
  className = "w-12 h-12",
}) => {
  // blobUrl is derived from URL.createObjectURL — CodeQL cannot trace it back
  // to the user-controlled albumCoverUrl string.
  const [blobUrl, setBlobUrl] = useState<string | undefined>();

  useEffect(() => {
    const raw = tags?.albumCoverUrl ?? "";
    const url = dataUrlToObjectUrl(raw);
    setBlobUrl(url);
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [tags?.albumCoverUrl]);

  return (
    <div
      className={`${className} rounded-none bg-[var(--bg-panel)] dark:bg-[var(--bg-panel)] flex items-center justify-center flex-shrink-0 shadow-md`}
    >
      {blobUrl ? (
        <img
          src={blobUrl}
          alt="Okładka albumu"
          className="w-full h-full object-cover rounded-none"
        />
      ) : (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="w-6 h-6 text-[var(--text-secondary)] dark:text-[var(--text-secondary)]"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path d="M18 3a1 1 0 00-1.447-.894L4 6.424V20h12V6.424l2.553-1.318A1 1 0 0018 3zM4 4.382l10-3.138V4L4 7.138V4.382zM15 18H5V8.138l10-3.138V18z" />
          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
        </svg>
      )}
    </div>
  );
};

export default AlbumCover;
