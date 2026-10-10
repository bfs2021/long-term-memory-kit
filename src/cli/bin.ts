#!/usr/bin/env bun
import { run } from "./run.ts";

const result = await run({ argv: process.argv.slice(2), cwd: process.cwd(), env: process.env });
process.stdout.write(result.stdout);
process.stderr.write(result.stderr);
// exitCode, not process.exit(): an early exit can truncate piped output.
process.exitCode = result.exitCode;
