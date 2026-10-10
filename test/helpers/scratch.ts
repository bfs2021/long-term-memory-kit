import { cp, mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

// Callback form, not a returned path: removal sits in `finally`, so a throwing
// test can't leak the dir and the caller can't forget cleanup.
export async function withScratch<T>(
  srcDir: string,
  fn: (dir: string) => Promise<T>,
): Promise<T> {
  const dir = await mkdtemp(join(tmpdir(), "ltm-scratch-"));
  try {
    await cp(srcDir, dir, { recursive: true });
    return await fn(dir);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}
