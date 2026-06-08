#!/bin/bash
# Usage: ./backup.sh user@vps-ip
# Run on your local machine

VPS=${1:-"user@your-vps-ip"}
DEST=~/moms-backup/music/

mkdir -p "$DEST"
rsync -avz --progress "${VPS}:/home/user/moms/music/" "$DEST"
