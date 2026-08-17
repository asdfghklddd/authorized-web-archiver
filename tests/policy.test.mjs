import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { isAllowedArchiveUrl, normalizeRecord } from "../lib/policy.js";

test("URL policy uses an exact local origin", () => {
  assert.equal(isAllowedArchiveUrl("http://127.0.0.1:8787/notes/1"), true);
  assert.equal(isAllowedArchiveUrl("https://127.0.0.1:8787/"), false);
  assert.equal(isAllowedArchiveUrl("http://127.0.0.1:8788/"), false);
  assert.equal(isAllowedArchiveUrl("http://127.0.0.1:8787.example.com/"), false);
});

test("record normalization truncates text and rejects remote input", () => {
  const record = normalizeRecord({ url: "http://127.0.0.1:8787/", title: "Demo", text: "x".repeat(120_000) });
  assert.equal(record.text.length, 100_000);
  assert.throws(() => normalizeRecord({ url: "https://example.com", title: "Demo", text: "text" }));
});

test("manifest keeps least-privilege permissions", async () => {
  const manifest = JSON.parse(await readFile(new URL("../manifest.json", import.meta.url), "utf8"));
  assert.deepEqual(manifest.permissions.sort(), ["activeTab", "nativeMessaging", "scripting"]);
  assert.equal("host_permissions" in manifest, false);
});

const walk = async (directory) => {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (entry.isDirectory() && entry.name === "__pycache__") continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(path)));
    else files.push(path);
  }
  return files;
};

test("implementation contains no private-platform or machine-path references", async () => {
  const folders = ["extension", "lib", "backend", "viewer", "demo"];
  const forbidden = [/worldquant/i, /phasebook/i, /C:\\Users\\/i, /\/Users\//i];
  for (const folder of folders) {
    const directory = fileURLToPath(new URL(`../${folder}`, import.meta.url));
    for (const file of await walk(directory)) {
      const content = await readFile(file, "utf8");
      for (const pattern of forbidden) assert.equal(pattern.test(content), false, `${pattern} found in ${file}`);
    }
  }
});
