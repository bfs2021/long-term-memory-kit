import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, test } from "bun:test";
import { withScratch } from "./scratch.ts";

const src = join(import.meta.dir, "scratch-src");

describe("withScratch", () => {
  test("hands fn a copy of the source at a different path", async () => {
    await withScratch(src, async (dir) => {
      expect(dir).not.toBe(src);
      for (const rel of ["a.txt", join("nested", "b.txt")]) {
        expect(readFileSync(join(dir, rel)).equals(readFileSync(join(src, rel)))).toBe(true);
      }
    });
  });

  test("writes inside the copy leave the source unchanged", async () => {
    await withScratch(src, async (dir) => {
      writeFileSync(join(dir, "a.txt"), "changed\n");
    });
    expect(readFileSync(join(src, "a.txt"), "utf8")).toBe("alpha\n");
  });

  test("removes the dir once withScratch resolves", async () => {
    let seen = "";
    await withScratch(src, async (dir) => {
      seen = dir;
      expect(existsSync(dir)).toBe(true);
    });
    expect(seen).not.toBe("");
    expect(existsSync(seen)).toBe(false);
  });

  test("propagates a throw from fn and still removes the dir", async () => {
    let seen = "";
    await expect(
      withScratch(src, async (dir) => {
        seen = dir;
        throw new Error("boom");
      }),
    ).rejects.toThrow("boom");
    expect(seen).not.toBe("");
    expect(existsSync(seen)).toBe(false);
  });
});
