import type { Track } from "../types";
import { keyMatchesFilter } from "./camelot";

type Filter = {
  search?: string;
  key?: string;
};

export function filterTracks(tracks: Track[], filter: Filter): Track[] {
  const search = (filter.search ?? "").trim().toLowerCase();
  const key = filter.key ?? "";
  return tracks.filter((track) => {
    const blob = `${track.title} ${track.artist}`.toLowerCase();
    if (search && !blob.includes(search)) return false;
    if (!keyMatchesFilter(track.key, key)) return false;
    return true;
  });
}

