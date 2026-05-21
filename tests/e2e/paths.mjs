import path from "node:path";
import { fileURLToPath } from "node:url";

export function resolveWorkspaceRoot(metaUrl) {
  const currentFile = fileURLToPath(metaUrl);
  return path.resolve(path.dirname(currentFile), "../..");
}
