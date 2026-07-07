#!/usr/bin/env bash
# Bring up GridScout's Postgres+PostGIS with ALL bulk data on the Expansion drive.
#
# Why this exists: /Volumes/Expansion is exFAT (no POSIX permissions), which cannot host
# a Postgres data dir or a container VM disk. Workaround: a mounted APFS sparse-image file
# that physically lives on Expansion but presents a real POSIX filesystem. Colima's VM lives
# inside it; Postgres data lives in a Docker named volume inside that VM.
#
# Idempotent: safe to re-run. Only the small colima/docker CLI binaries touch the internal disk.
set -euo pipefail

IMAGE_FILE="/Volumes/Expansion/gridscout-data.sparseimage"
MOUNT="/Volumes/gridscout-data"
IMAGE_SIZE="40g"
export COLIMA_HOME="$MOUNT/colima"
export LIMA_HOME="$MOUNT/lima"
# Talk straight to Colima's docker socket, and use a CLEAN docker config on the image so
# docker doesn't invoke a stale `docker-credential-desktop` helper (leftover Docker Desktop
# config on the internal disk) — that breaks even anonymous public-image pulls.
export DOCKER_HOST="unix://$COLIMA_HOME/docker.sock"
export DOCKER_CONFIG="$MOUNT/docker-config"

log() { printf '\033[36m[db-up]\033[0m %s\n' "$*"; }

# 1) APFS sparse image on Expansion
if [ ! -e "$IMAGE_FILE" ]; then
  log "creating APFS sparse image $IMAGE_FILE ($IMAGE_SIZE)"
  hdiutil create -size "$IMAGE_SIZE" -type SPARSE -fs "Case-sensitive APFS" \
    -volname gridscout-data "$IMAGE_FILE" >/dev/null
fi

# 2) mount it (hdiutil auto-mounts to /Volumes/<volname>)
if [ ! -d "$MOUNT" ]; then
  log "mounting image at $MOUNT"
  hdiutil attach "$IMAGE_FILE" >/dev/null
fi
mkdir -p "$COLIMA_HOME" "$LIMA_HOME" "$DOCKER_CONFIG"
[ -f "$DOCKER_CONFIG/config.json" ] || printf '{}\n' > "$DOCKER_CONFIG/config.json"

# 3) ensure container tooling (small binaries via existing Homebrew)
for f in colima docker docker-compose; do
  if ! command -v "$f" >/dev/null 2>&1; then
    log "installing $f via Homebrew"
    brew install "$f"
  fi
done

# 4) start Colima (VM home is on the Expansion-backed image)
if ! colima status >/dev/null 2>&1; then
  log "starting Colima VM (first run downloads a Linux image — a few minutes)"
  colima start --cpu 2 --memory 4 --disk 30
else
  log "Colima already running"
fi

# 5) start Postgres+PostGIS
log "starting postgis container"
docker-compose up -d

# 6) wait for readiness
log "waiting for Postgres to accept connections"
for _ in $(seq 1 60); do
  if docker-compose exec -T db pg_isready -U gridscout -d gridscout >/dev/null 2>&1; then
    log "Postgres is ready."
    exit 0
  fi
  sleep 2
done
log "ERROR: Postgres did not become ready in time"
exit 1
