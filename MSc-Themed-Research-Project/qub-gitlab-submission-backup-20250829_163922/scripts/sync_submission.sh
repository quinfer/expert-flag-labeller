#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUBMISSION_DIR="$PROJECT_ROOT/qub-gitlab-submission"

mkdir -p "$SUBMISSION_DIR" "$SUBMISSION_DIR/docs" "$SUBMISSION_DIR/scripts" "$SUBMISSION_DIR/data" "$SUBMISSION_DIR/final_code"

# Top-level files
rsync -a "$PROJECT_ROOT/README.md" "$SUBMISSION_DIR/"

# Docs (exclude heavy papers/PDFs)
rsync -a \
  --exclude "papers/**" \
  --exclude "*.pdf" \
  "$PROJECT_ROOT/docs/" "$SUBMISSION_DIR/docs/"

# Scripts
rsync -a "$PROJECT_ROOT/scripts/" "$SUBMISSION_DIR/scripts/"

# Data (exclude heavy assets and derived outputs)
rsync -a \
  --exclude "ni_flags*/" \
  --exclude "annotations/" \
  --exclude "images/" \
  --exclude "processed/" \
  --exclude "output/" \
  --exclude "archive/" \
  --exclude "__pycache__/" \
  --exclude ".ipynb_checkpoints/" \
  "$PROJECT_ROOT/data/" "$SUBMISSION_DIR/data/"

# Upstream baseline code (no caches)
rsync -a \
  --exclude "__pycache__/" \
  --exclude ".ipynb_checkpoints/" \
  "$PROJECT_ROOT/final_code/" "$SUBMISSION_DIR/final_code/"

echo "Synced to: $SUBMISSION_DIR"
