import { describe, it, expect } from "vitest";
import { getCompatibleKeys, isBpmCompatible } from "./djUtils";

describe("getCompatibleKeys", () => {
  it("returns same key, relative, and neighbours for 8A", () => {
    const keys = getCompatibleKeys("8A");
    expect(keys).toContain("8A");   // exact
    expect(keys).toContain("8B");   // relative major
    expect(keys).toContain("7A");   // -1 hour
    expect(keys).toContain("9A");   // +1 hour
    expect(keys).toHaveLength(4);
  });

  it("wraps correctly at boundary 1A → 12A and 2A", () => {
    const keys = getCompatibleKeys("1A");
    expect(keys).toContain("12A"); // -1 wraps to 12
    expect(keys).toContain("2A");  // +1
  });

  it("wraps correctly at boundary 12B → 11B and 1B", () => {
    const keys = getCompatibleKeys("12B");
    expect(keys).toContain("11B");
    expect(keys).toContain("1B"); // +1 wraps to 1
  });

  it("is case-insensitive", () => {
    expect(getCompatibleKeys("8a")).toContain("8A");
    expect(getCompatibleKeys("8b")).toContain("8B");
  });

  it("returns empty array for unknown key", () => {
    expect(getCompatibleKeys("")).toHaveLength(0);
    expect(getCompatibleKeys("X#")).toHaveLength(0);
    expect(getCompatibleKeys("13A")).toHaveLength(0);
  });
});

describe("isBpmCompatible", () => {
  it("returns true within default 5% range", () => {
    expect(isBpmCompatible(140, 143)).toBe(true);   // diff = 3, threshold = 7
    expect(isBpmCompatible(140, 147)).toBe(true);   // exactly on threshold
  });

  it("returns false outside default 5% range", () => {
    expect(isBpmCompatible(140, 160)).toBe(false);  // diff = 20 > 7
  });

  it("respects custom range percent", () => {
    expect(isBpmCompatible(140, 160, 15)).toBe(true);  // threshold = 21
    expect(isBpmCompatible(140, 160, 10)).toBe(false); // threshold = 14
  });

  it("returns false when bpm is undefined or zero", () => {
    expect(isBpmCompatible(undefined, 140)).toBe(false);
    expect(isBpmCompatible(140, undefined)).toBe(false);
    expect(isBpmCompatible(0, 140)).toBe(false);
  });

  it("matches halfspeed tracks (70 vs 140)", () => {
    // 70 BPM is not within 5% of 140 — DJ must explicitly halve
    expect(isBpmCompatible(70, 140)).toBe(false);
  });
});
