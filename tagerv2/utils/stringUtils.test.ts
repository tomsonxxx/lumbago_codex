import { describe, it, expect } from "vitest";
import { levenshteinDistance, calculateSimilarity } from "./stringUtils";

describe("levenshteinDistance", () => {
  it("returns 0 for identical strings", () => {
    expect(levenshteinDistance("techno", "techno")).toBe(0);
  });

  it("returns length for empty vs non-empty", () => {
    expect(levenshteinDistance("", "abc")).toBe(3);
    expect(levenshteinDistance("abc", "")).toBe(3);
  });

  it("counts single substitution", () => {
    expect(levenshteinDistance("cat", "bat")).toBe(1);
  });

  it("counts single insertion", () => {
    expect(levenshteinDistance("car", "cars")).toBe(1);
  });

  it("counts multiple operations", () => {
    expect(levenshteinDistance("kitten", "sitting")).toBe(3);
  });
});

describe("calculateSimilarity", () => {
  it("returns 1.0 for identical strings (case-insensitive)", () => {
    expect(calculateSimilarity("Techno", "techno")).toBe(1.0);
    expect(calculateSimilarity("BPM", "bpm")).toBe(1.0);
  });

  it("returns 0.0 when one string is empty", () => {
    expect(calculateSimilarity("", "something")).toBe(0.0);
    expect(calculateSimilarity("something", "")).toBe(0.0);
  });

  it("returns high similarity for near-matches", () => {
    // "sunrise" vs "sunrise (original mix)" — should be > 0.5
    const sim = calculateSimilarity("sunrise", "sunrise original mix");
    expect(sim).toBeGreaterThan(0.3);
  });

  it("returns low similarity for completely different strings", () => {
    const sim = calculateSimilarity("techno", "jazz");
    expect(sim).toBeLessThan(0.5);
  });

  it("is symmetric", () => {
    const ab = calculateSimilarity("midnight", "midnigth");
    const ba = calculateSimilarity("midnigth", "midnight");
    expect(ab).toBeCloseTo(ba, 5);
  });
});
