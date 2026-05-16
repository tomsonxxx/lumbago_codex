import { describe, it, expect } from "vitest";
import { findDuplicateSets } from "./duplicateUtils";
import type { AudioFile } from "../types";

// Minimal AudioFile factory for tests
function makeFile(id: string, artist: string, title: string): AudioFile {
  return {
    id,
    file: { name: `${artist} - ${title}.mp3` } as File,
    originalTags: { artist, title, albumArtist: artist },
    fetchedTags: null,
    status: "idle",
    processingStage: null,
    selected: false,
    playlistIds: [],
  } as unknown as AudioFile;
}

describe("findDuplicateSets", () => {
  it("returns empty map for no files", () => {
    expect(findDuplicateSets([])).toEqual(new Map());
  });

  it("returns empty map for unique files", () => {
    const files = [
      makeFile("1", "Artist A", "Track One"),
      makeFile("2", "Artist B", "Track Two"),
    ];
    const result = findDuplicateSets(files);
    expect(result.size).toBe(0);
  });

  it("groups exact artist+title duplicates", () => {
    const files = [
      makeFile("1", "Daft Punk", "One More Time"),
      makeFile("2", "Daft Punk", "One More Time"),
      makeFile("3", "Daft Punk", "Harder Better"),
    ];
    const result = findDuplicateSets(files);
    expect(result.size).toBe(1);
    const [group] = result.values();
    expect(group).toHaveLength(2);
    expect(group.map((f) => f.id)).toContain("1");
    expect(group.map((f) => f.id)).toContain("2");
  });

  it("groups case-insensitive duplicates", () => {
    const files = [
      makeFile("1", "daft punk", "one more time"),
      makeFile("2", "Daft Punk", "One More Time"),
    ];
    const result = findDuplicateSets(files);
    expect(result.size).toBe(1);
  });

  it("does not group different tracks by same artist", () => {
    const files = [
      makeFile("1", "Daft Punk", "One More Time"),
      makeFile("2", "Daft Punk", "Harder Better Faster"),
    ];
    expect(findDuplicateSets(files).size).toBe(0);
  });
});
