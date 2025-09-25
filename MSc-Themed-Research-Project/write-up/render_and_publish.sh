#!/usr/bin/env bash
# Render the Quarto thesis PDF and copy to the submission folder

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
WRITEUP_DIR="$SCRIPT_DIR"
REPO_ROOT="$(cd "$WRITEUP_DIR/../.." && pwd)"

# Defaults
SOURCE_QMD_DEFAULT="$WRITEUP_DIR/complete_quarto_paper.qmd"
OUTPUT_PDF_DEFAULT="$WRITEUP_DIR/complete_quarto_paper.pdf"
DEST_DEFAULT="$REPO_ROOT/docs/thesis_paper.pdf"

# Args: [source_qmd] [dest_pdf]
SOURCE_QMD="${1:-$SOURCE_QMD_DEFAULT}"
DEST_PDF="${2:-$DEST_DEFAULT}"
OUTPUT_PDF="$OUTPUT_PDF_DEFAULT"

usage() {
  cat <<USAGE
Usage: $(basename "$0") [source_qmd] [dest_pdf]

Defaults:
  source_qmd: $SOURCE_QMD_DEFAULT
  dest_pdf  : $DEST_DEFAULT

Examples:
  $(basename "$0")
  $(basename "$0") $SOURCE_QMD_DEFAULT $DEST_DEFAULT
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v quarto >/dev/null 2>&1; then
  echo "Error: quarto not found in PATH. Please install Quarto and try again." >&2
  exit 1
fi

if [[ ! -f "$SOURCE_QMD" ]]; then
  echo "Error: source QMD not found: $SOURCE_QMD" >&2
  exit 1
fi

echo "Rendering: $SOURCE_QMD"
(
  cd "$WRITEUP_DIR"
  quarto render "$SOURCE_QMD" --to pdf
)

if [[ ! -f "$OUTPUT_PDF" ]]; then
  echo "Error: expected output PDF not found: $OUTPUT_PDF" >&2
  exit 1
fi

dest_dir="$(dirname "$DEST_PDF")"
mkdir -p "$dest_dir"

# Optional timestamped backup of existing destination
if [[ -f "$DEST_PDF" ]]; then
  ts="$(date +%Y%m%d_%H%M%S)"
  backup="${DEST_PDF%.pdf}_backup_${ts}.pdf"
  cp -p "$DEST_PDF" "$backup" || true
  echo "Backup created: $backup"
fi

cp -f "$OUTPUT_PDF" "$DEST_PDF"

echo "Rendered PDF: $OUTPUT_PDF"
echo "Published to : $DEST_PDF"
echo "Done."
