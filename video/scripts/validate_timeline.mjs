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

  // 2. Pre-Render Story & Narrative Consistency Gate
  const bannedGenericTokens = [
    'invariant algorithmic',
    'boilerplate state',
    'acme vector',
  ];

  const bannedMLTokens = [
    'k-means',
    'kmeans',
    'dbscan',
    't-sne',
    'tsne',
  ];

  const sourceDoc = (
    jsonData.source_text ||
    jsonData.source_document ||
    ''
  ).toLowerCase();
  const topicStr = (jsonData.topic || jsonData.title || '').toLowerCase();
  const subjectStr = (jsonData.subject || '').toLowerCase();

  const bannedTokens = [...bannedGenericTokens];
  if (subjectStr !== 'ml') {
    bannedTokens.push(...bannedMLTokens);
  }

  const narrativeErrors = [];

  (jsonData.scenes || []).forEach((scene, idx) => {
    const sceneId = scene.scene_id || scene.id || `scene_${idx + 1}`;
    const sceneStr = JSON.stringify(scene).toLowerCase();

    // Check banned placeholder tokens
    for (const token of bannedTokens) {
      if (sceneStr.includes(token)) {
        if (!sourceDoc.includes(token) && !topicStr.includes(token)) {
          narrativeErrors.push(
            `Scene ${idx} (${sceneId}) contains banned placeholder token '${token}' not found in source document or topic.`
          );
        }
      }
    }

    // Check spoken narration syntax
    const narration = scene.spoken_text || scene.narration || scene.narration_text || '';
    if (narration) {
      const scopeMatch = narration.match(/@[a-zA-Z0-9_\-\./]+/);
      if (scopeMatch) {
        narrativeErrors.push(
          `Scene ${idx} (${sceneId}) spoken narration contains raw package symbol '${scopeMatch[0]}'. Decouple spoken narration from visual syntax.`
        );
      }
      const flagMatch = narration.match(/(?:^|\s)--[a-zA-Z0-9_\-]+/);
      if (flagMatch) {
        narrativeErrors.push(
          `Scene ${idx} (${sceneId}) spoken narration contains raw CLI flag '${flagMatch[0].trim()}'. Spoken narration must be natural English.`
        );
      }
      const slashMatch = narration.match(/\b(at\s+[a-zA-Z0-9_-]+\s+slash\s+[a-zA-Z0-9_-]+)\b/i);
      if (slashMatch) {
        narrativeErrors.push(
          `Scene ${idx} (${sceneId}) spoken narration contains literal phonetic symbol '${slashMatch[0]}'.`
        );
      }
    }
  });

  if (narrativeErrors.length > 0) {
    const errorPayload = {
      stage: 'narrative_gate',
      scene_id: null,
      field_path: 'scenes',
      message: 'Pre-render narrative consistency check failed',
      all_errors: narrativeErrors.map(msg => ({ path: 'scenes', message: msg })),
      timestamp: new Date().toISOString(),
    };

    const errorFilePath = path.join(runDir, 'validation.error.json');
    fs.writeFileSync(errorFilePath, JSON.stringify(errorPayload, null, 2));

    console.error(`[NARRATIVE:ERROR] Story & fact consistency check failed:`);
    narrativeErrors.forEach((msg) => {
      console.error(`  • ${msg}`);
    });
    console.error(`[NARRATIVE:ERROR] Diagnostics written to: ${errorFilePath}`);
    process.exit(1);
  }

  const sceneCount = (jsonData.scenes && jsonData.scenes.length) || 0;
  console.log(`[ZOD:SUCCESS] Timeline validation passed for run '${jsonData.run_id}' (${sceneCount} scenes).`);
  process.exit(0);
}

main();
