import { expect, test } from "bun:test";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { run } from "../../src/cli/run.ts";

const repoRoot = fileURLToPath(new URL("../..", import.meta.url));

function spawnBin(argv: string[]) {
  return spawnSync(process.execPath, ["src/cli/bin.ts", ...argv], {
    encoding: "utf8",
    cwd: repoRoot,
  });
}

test("--version through the wrapper matches the in-process result", async () => {
  const expected = await run({ argv: ["--version"], cwd: repoRoot, env: process.env });
  const spawned = spawnBin(["--version"]);
  expect(spawned.stdout).toBe(expected.stdout);
  expect(spawned.status).toBe(expected.exitCode);
});

test("unknown command exits 2 with the name on stderr", async () => {
  const expected = await run({ argv: ["no-such-command"], cwd: repoRoot, env: process.env });
  const spawned = spawnBin(["no-such-command"]);
  expect(spawned.status).toBe(2);
  expect(spawned.stderr).toContain("no-such-command");
  expect(spawned.stderr).toBe(expected.stderr);
});
