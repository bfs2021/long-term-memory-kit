#!/usr/bin/env bun
import { run } from "./run.ts";

const r = await run({ argv: process.argv.slice(2), cwd: process.cwd(), env: process.env });
process.stdout.write(r.stdout);
process.stderr.write(r.stderr);
// exitCode, not process.exit(): an early exit can truncate piped output.
process.exitCode = r.exitCode;
