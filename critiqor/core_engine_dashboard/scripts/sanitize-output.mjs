import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dashboardRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputRoot = path.join(dashboardRoot, ".output");
const absolutePrefix = `${dashboardRoot}${path.sep}`;
const absolutePrefixPosix = `${dashboardRoot.split(path.sep).join("/")}/`;

function walk(dir, files = []) {
  if (!fs.existsSync(dir)) return files;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const next = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(next, files);
    else files.push(next);
  }
  return files;
}

function sanitize(text) {
  return text
    .split(absolutePrefix).join("")
    .split(absolutePrefixPosix).join("")
    .replace(/\/Users\/[^"'`\s]+\/core_engine_dashboard\//g, "")
    .replace(/\/home\/[^"'`\s]+\/core_engine_dashboard\//g, "");
}

let changed = 0;
for (const file of walk(outputRoot)) {
  if (!/\.(mjs|js|cjs|json|map)$/.test(file)) continue;
  const original = fs.readFileSync(file, "utf8");
  const next = sanitize(original);
  if (next !== original) {
    fs.writeFileSync(file, next);
    changed += 1;
  }
}

if (changed) {
  console.log(`Sanitized machine paths from ${changed} dashboard output file(s).`);
}
