#!/usr/bin/env bash
set -euo pipefail

# Placeholder URL. Set RS5M ViT-H-14 checkpoint URL here.
CKPT_URL="<PUT_RS5M_VITH14_URL_HERE>"
OUT_DIR="$(cd "$(dirname "$0")/.." && pwd)/final_code/checkpoints"
OUT_FILE="$OUT_DIR/RS5M_ViT-H-14.pt"

mkdir -p "$OUT_DIR"

if [[ "$CKPT_URL" == "<PUT_RS5M_VITH14_URL_HERE>" ]]; then
  echo "Please edit scripts/download_rs5m_checkpoint.sh and set CKPT_URL to the RS5M ViT-H-14 link."
  exit 1
fi

echo "Downloading RS5M ViT-H-14 to: $OUT_FILE"
curl -L "$CKPT_URL" -o "$OUT_FILE"
echo "Done."
