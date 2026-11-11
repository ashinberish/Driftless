import { describe, expect, it } from "vitest";

import { formatBytes, formatCount } from "./format";

describe("formatBytes", () => {
  it.each([
    [null, "—"],
    [512, "512 B"],
    [1536, "1.5 KB"],
    [212 * 1024 ** 3, "212 GB"],
    [1.8 * 1024 ** 4, "1.8 TB"],
  ])("%s → %s", (input, expected) => {
    expect(formatBytes(input)).toBe(expected);
  });
});

describe("formatCount", () => {
  it("uses compact notation for large numbers", () => {
    expect(formatCount(950)).toBe("950");
    expect(formatCount(48_200_000)).toBe("48M");
    expect(formatCount(undefined)).toBe("—");
  });
});
