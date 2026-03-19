import { describe, expect, it } from "vitest";
import { keyMatchesFilter, toCamelot } from "../src/utils/camelot";

describe("camelot mapping", () => {
  it("maps musical key to camelot", () => {
    expect(toCamelot("Am")).toBe("8A");
    expect(toCamelot("A minor")).toBe("8A");
    expect(toCamelot("C")).toBe("8B");
  });

  it("accepts camelot input as-is", () => {
    expect(toCamelot("10b")).toBe("10B");
  });

  it("matches filter across aliases", () => {
    expect(keyMatchesFilter("Am", "8A")).toBe(true);
    expect(keyMatchesFilter("A minor", "8A")).toBe(true);
    expect(keyMatchesFilter("C", "8A")).toBe(false);
  });
});

