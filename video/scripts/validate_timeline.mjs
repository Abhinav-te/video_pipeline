#!/usr/bin/env node
/**
 * video/scripts/validate_timeline.mjs
 * Pre-render Node.js Zod Timeline Validation Gate.
 *
 * Validates runs/<run_id>/data.json against TimelineSchema before Remotion rendering.
 * On failure, writes <run_dir>/validation.error.json and exits non-zero.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { TimelineSchema } from '../src/schema/timelineSchema.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error('Usage: node video/scripts/validate_timeline.mjs <path/to/data.json>');
    process.exit(1);
  }

  const dataPath = path.resolve(args[0]);
  if (!fs.existsSync(dataPath)) {
    console.error(`[ZOD:ERROR] data.json not found: ${dataPath}`);
    process.exit(1);
  }

  const runDir = path.dirname(dataPath);

  let raw;
  try {
    raw = fs.readFileSync(dataPath, 'utf-8');
  } catch (err) {
    console.error(`[ZOD:ERROR] Failed reading data.json: ${err.message}`);
    process.exit(1);
  }

  let jsonData;
  try {
    jsonData = JSON.parse(raw);
  } catch (err) {
    const errorPayload = {
      stage: 'zod_gate',
      scene_id: null,
      field_path: 'root',
      message: `Invalid JSON syntax: ${err.message}`,
      timestamp: new Date().toISOString(),
    };
    fs.writeFileSync(
      path.join(runDir, 'validation.error.json'),
      JSON.stringify(errorPayload, null, 2)
    );
    console.error(`[ZOD:ERROR] JSON parsing failed: ${err.message}`);
    process.exit(1);
  }

  const result = TimelineSchema.safeParse(jsonData);

  if (!result.success) {
    const firstIssue = result.error.issues[0] || {};
    const fieldPath = firstIssue.path ? firstIssue.path.join('.') : 'unknown';
    
    // Find scene_id if error is within a scene
    let sceneId = null;
    if (firstIssue.path && firstIssue.path[0] === 'scenes' && typeof firstIssue.path[1] === 'number') {
      const sceneObj = jsonData.scenes && jsonData.scenes[firstIssue.path[1]];
      sceneId = sceneObj ? (sceneObj.scene_id || sceneObj.id || firstIssue.path[1]) : firstIssue.path[1];
    }

    const errorPayload = {
      stage: 'zod_gate',
      scene_id: sceneId,
      field_path: fieldPath,
      message: firstIssue.message || 'Timeline schema validation failed',
      all_errors: result.error.issues.map(i => ({
        path: i.path.join('.'),
        message: i.message,
      })),
      timestamp: new Date().toISOString(),
    };

    const errorFilePath = path.join(runDir, 'validation.error.json');
    fs.writeFileSync(errorFilePath, JSON.stringify(errorPayload, null, 2));

    console.error(`[ZOD:ERROR] TimelineSchema validation failed at '${fieldPath}': ${errorPayload.message}`);
    result.error.issues.forEach((issue) => {
      console.error(`  • [${issue.path.join('.')}] ${issue.message}`);
    });
    console.error(`[ZOD:ERROR] Diagnostics written to: ${errorFilePath}`);
    process.exit(1);
  }

  const sceneCount = (jsonData.scenes && jsonData.scenes.length) || 0;
  console.log(`[ZOD:SUCCESS] Timeline validation passed for run '${jsonData.run_id}' (${sceneCount} scenes).`);
  process.exit(0);
}

main();
