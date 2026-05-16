import { describe, expect, it } from "vitest";
import type { Track } from "../types";
import { filterTracks } from "./filterTracks";

const TRACKS: Track[] = [
  { id: 1, title: "One More Time", artist: "Daft Punk", key: "8B" },
  { id: 2, title: "Blue (Da Ba Dee)", artist: "Eiffel 65", key: "8A" },
  { id: 3, title: "Sandstorm", artist: "Darude", key: "9B" },
];

describe("filterTracks", () => {
  it("returns all tracks when no filter applied", () => {
    expect(filterTracks(TRACKS, {})).toHaveLength(3);
  });

  it("filters by search term in title", () => {
    const result = filterTracks(TRACKS, { search: "sandstorm" });
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("Sandstorm");
  });

  it("filters by search term in artist", () => {
    const result = filterTracks(TRACKS, { search: "daft" });
    expect(result).toHaveLength(1);
    expect(result[0].artist).toBe("Daft Punk");
  });

  it("search is case-insensitive", () => {
    expect(filterTracks(TRACKS, { search: "DARUDE" })).toHaveLength(1);
  });

  it("returns empty array when search matches nothing", () => {
    expect(filterTracks(TRACKS, { search: "xyz_no_match" })).toHaveLength(0);
  });

  it("filters by Camelot key", () => {
    const result = filterTracks(TRACKS, { key: "8A" });
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("Blue (Da Ba Dee)");
  });

  it("ignores empty key filter", () => {
    expect(filterTracks(TRACKS, { key: "" })).toHaveLength(3);
  });

  it("combines search and key filters", () => {
    const result = filterTracks(TRACKS, { search: "daft", key: "8B" });
    expect(result).toHaveLength(1);
    expect(result[0].title).toBe("One More Time");
  });

  it("combined filter returns empty when key doesn't match", () => {
    const result = filterTracks(TRACKS, { search: "daft", key: "8A" });
    expect(result).toHaveLength(0);
  });
});
