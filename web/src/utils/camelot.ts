const MUSICAL_TO_CAMELOT: Record<string, string> = {
  C: "8B",
  G: "9B",
  D: "10B",
  A: "11B",
  E: "12B",
  B: "1B",
  "F#": "2B",
  "C#": "3B",
  "G#": "4B",
  "D#": "5B",
  "A#": "6B",
  F: "7B",
  Am: "8A",
  Em: "9A",
  Bm: "10A",
  "F#m": "11A",
  "C#m": "12A",
  "G#m": "1A",
  "D#m": "2A",
  "A#m": "3A",
  Fm: "4A",
  Cm: "5A",
  Gm: "6A",
  Dm: "7A"
};

function normalizeMusicalKey(raw: string): string {
  const value = raw.trim().toLowerCase().replace(/\s+/g, " ");
  if (!value) return "";
  const base = value
    .replace(" major", "")
    .replace(" minor", "m")
    .replace(" min", "m")
    .replace("maj", "");
  return base.charAt(0).toUpperCase() + base.slice(1);
}

export function toCamelot(rawKey: string): string | null {
  const trimmed = rawKey.trim().toUpperCase();
  if (/^(1[0-2]|[1-9])[AB]$/.test(trimmed)) {
    return trimmed;
  }
  const normalized = normalizeMusicalKey(rawKey);
  return MUSICAL_TO_CAMELOT[normalized] ?? null;
}

export function keyMatchesFilter(trackKey: string | undefined, filterKey: string): boolean {
  if (!filterKey.trim()) return true;
  if (!trackKey?.trim()) return false;
  const left = toCamelot(trackKey);
  const right = toCamelot(filterKey);
  if (!left || !right) return false;
  return left === right;
}

