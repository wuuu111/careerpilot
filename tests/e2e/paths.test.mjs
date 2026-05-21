import test from "node:test";
import assert from "node:assert/strict";

import { resolveWorkspaceRoot } from "./paths.mjs";

test("resolveWorkspaceRoot derives repo root from the smoke script location", () => {
  const root = resolveWorkspaceRoot(import.meta.url);

  assert.equal(root.endsWith("/careerpilot"), true);
  assert.equal(root.includes("/tests/e2e"), false);
});
