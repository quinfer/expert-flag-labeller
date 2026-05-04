#!/usr/bin/env node
/**
 * Move items to the BACK of static-images-audit.json where Brandon used
 * "Flag for review" → **Other** (the second radio next to "Complex case").
 *
 * Those rows are stored with needs_review = true and review_reason = 'Other'.
 *
 * Prereq: .env.local with NEXT_PUBLIC_SUPABASE_URL and a key that can
 * read (and optionally delete) rows in `classifications`:
 *   SUPABASE_SERVICE_ROLE_KEY  (preferred), or SUPABASE_SERVICE_KEY from .env.example
 *
 * Usage:
 *   node scripts/requeue-brandon-flag-other.mjs --dry-run
 *   node scripts/requeue-brandon-flag-other.mjs
 *   node scripts/requeue-brandon-flag-other.mjs --delete-classifications
 *
 * Flags:
 *   --dry-run                       Print matches only; do not write JSON or delete
 *   --delete-classifications        After writing JSON, delete classification rows only for images
 *                                   that appear in static-images-audit.json (same set as “move to back”).
 *   --delete-all-matched-rows       With --delete-classifications: also delete “orphan” matches not in
 *                                   the audit file (default without this flag: do not delete those).
 *   --since-days=N                  Only consider classifications from the last N days (default: all)
 */

import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..');
const AUDIT_PATH = path.join(root, 'src', 'data', 'static-images-audit.json');

dotenv.config({ path: path.join(root, '.env.local') });
dotenv.config({ path: path.join(root, '.env') });

function normTown(t) {
  return String(t ?? '')
    .trim()
    .toUpperCase()
    .replace(/ /g, '_');
}

function rowKey(town, imageId) {
  return `${normTown(town)}|${String(imageId ?? '').trim()}`;
}

/** In-app: Flag for review → radio value "Other" (label "Other reason"). */
function rowMatchesReviewOther(row) {
  const rr = String(row.review_reason ?? '').trim();
  return rr === 'Other' || /^other$/i.test(rr);
}

function parseArgs(argv) {
  let dryRun = false;
  let deleteClassifications = false;
  let deleteAllMatchedRows = false;
  let sinceDays = null;

  for (const a of argv) {
    if (a === '--dry-run') dryRun = true;
    if (a === '--delete-classifications') deleteClassifications = true;
    if (a === '--delete-all-matched-rows') deleteAllMatchedRows = true;
    const m = /^--since-days=(\d+)$/.exec(a);
    if (m) sinceDays = Number(m[1]);
  }

  return { dryRun, deleteClassifications, deleteAllMatchedRows, sinceDays };
}

async function main() {
  const { dryRun, deleteClassifications, deleteAllMatchedRows, sinceDays } = parseArgs(
    process.argv.slice(2)
  );

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey =
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const key = serviceKey || anonKey;

  if (!url || !key) {
    console.error(
      'Missing NEXT_PUBLIC_SUPABASE_URL or Supabase key. Set SUPABASE_SERVICE_ROLE_KEY (recommended) in .env.local'
    );
    process.exit(1);
  }

  if (!serviceKey) {
    console.warn(
      'Warning: using anon key — reads/deletes may fail if RLS blocks. Prefer SUPABASE_SERVICE_ROLE_KEY.'
    );
  }

  const supabase = createClient(url, key);
  let q = supabase
    .from('classifications')
    .select(
      'id, image_id, town, specific_flag, user_content, needs_review, review_reason, timestamp, expert_id'
    )
    .eq('expert_id', 'Brandon')
    .eq('needs_review', true)
    .eq('review_reason', 'Other')
    .order('timestamp', { ascending: false });

  if (sinceDays != null && sinceDays > 0) {
    const cutoff = new Date(Date.now() - sinceDays * 864e5).toISOString();
    q = q.gte('timestamp', cutoff);
  }

  const { data: rows, error } = await q;

  if (error) {
    console.error('Supabase error:', error.message);
    process.exit(1);
  }

  const matches = (rows || []).filter(rowMatchesReviewOther);

  console.log(`Brandon rows (needs_review + reason "Other"): ${(rows || []).length}`);
  console.log(`Re-queue targets (after normalizing reason): ${matches.length}`);

  if (matches.length === 0) {
    console.log('Nothing to re-queue. Exiting.');
    process.exit(0);
  }

  const matchKeys = new Set(matches.map((r) => rowKey(r.town, r.image_id)));

  for (const r of matches.slice(0, 20)) {
    console.log(
      `  - ${r.image_id} | review_reason=${JSON.stringify(r.review_reason)} | flag=${r.specific_flag || '(none)'}`
    );
  }
  if (matches.length > 20) console.log(`  ... and ${matches.length - 20} more`);

  if (!fs.existsSync(AUDIT_PATH)) {
    console.error('Audit file not found:', AUDIT_PATH);
    process.exit(1);
  }

  const audit = JSON.parse(fs.readFileSync(AUDIT_PATH, 'utf8'));
  if (!Array.isArray(audit)) {
    console.error('static-images-audit.json must be a JSON array');
    process.exit(1);
  }

  const stay = [];
  const move = [];
  for (const img of audit) {
    const k = rowKey(img.town, img.filename);
    if (matchKeys.has(k)) move.push(img);
    else stay.push(img);
  }

  console.log(`Audit length: ${audit.length}; stay: ${stay.length}; move to back: ${move.length}`);

  const unmatchedKeys = [...matchKeys].filter((k) => !audit.some((img) => rowKey(img.town, img.filename) === k));
  if (unmatchedKeys.length) {
    console.warn(
      `${unmatchedKeys.length} matched classification(s) not found in audit JSON (already absent or town/filename mismatch):`
    );
    unmatchedKeys.slice(0, 10).forEach((k) => console.warn('   ', k));
    if (unmatchedKeys.length > 10) console.warn('   ...');
  }

  const newAudit = [...stay, ...move];

  const auditKeys = new Set(audit.map((img) => rowKey(img.town, img.filename)));
  const matchesInAudit = matches.filter((r) => auditKeys.has(rowKey(r.town, r.image_id)));
  const matchesOrphan = matches.filter((r) => !auditKeys.has(rowKey(r.town, r.image_id)));

  if (dryRun) {
    console.log('\n--- Dry run (no file changes, no database deletes) ---');
    console.log(
      `Would move ${move.length} image(s) to the end of static-images-audit.json (of ${matches.length} matching Supabase row(s)).`
    );
    console.log(
      `With --delete-classifications (default): would delete ${matchesInAudit.length} row(s) tied to those audit images (not ${matchesOrphan.length} orphan match(es) without --delete-all-matched-rows).`
    );
    if (deleteAllMatchedRows) {
      console.log(`With --delete-all-matched-rows: would delete all ${matches.length} matching row(s).`);
    }
    process.exit(0);
  }

  fs.writeFileSync(AUDIT_PATH, JSON.stringify(newAudit, null, 2) + '\n', 'utf8');
  console.log('Wrote reordered queue to', AUDIT_PATH);

  if (deleteClassifications && matches.length) {
    const toDelete = deleteAllMatchedRows ? matches : matchesInAudit;
    if (!deleteAllMatchedRows && matchesOrphan.length) {
      console.log(
        `Skipping ${matchesOrphan.length} orphan classification row(s) (not in audit). Use --delete-all-matched-rows to delete them too.`
      );
    }
    const ids = toDelete.map((r) => r.id).filter(Boolean);
    if (!ids.length) {
      console.log('No classification rows in delete set; nothing to delete.');
    } else {
      const { error: delErr } = await supabase.from('classifications').delete().in('id', ids);
      if (delErr) {
        console.error('Delete error:', delErr.message);
        process.exit(1);
      }
      console.log(`Deleted ${ids.length} classification row(s) for Brandon so he can re-save.`);
    }
  } else if (!deleteClassifications && move.length) {
    console.log(
      '\nNote: Brandon still has saved rows for these images — the app will block re-save (409). Re-run with --delete-classifications after reviewing, or delete rows in Supabase manually.'
    );
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
