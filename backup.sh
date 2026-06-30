#!/bin/bash
# Usage: ./backup.sh [user@vps-ip]
# Run on your local machine. SSH on VPS listens on port 8122.

VPS=${1:-"openclaw@95.85.229.224"}
DEST=~/moms-backup/music/

mkdir -p "$DEST"
rsync -avz --progress -e "ssh -p 8122" "${VPS}:/home/openclaw/moms/music/" "$DEST"
