#!/usr/bin/env bash
# Example: copy VeraCrypt container + keyfile between lab hosts when volumes are UNMOUNTED.
# Copy to docs/private/scripts/ or adapt locally — do not commit real hostnames/paths to GitHub.
set -euo pipefail

# shellcheck disable=SC2034
SOURCE_HOST="REPLACE_SOURCE_SHORTNAME"
TARGET_HOST="REPLACE_TARGET_SHORTNAME"
REMOTE_USER="REPLACE_SSH_USER"
SRC_DIR="REPLACE_PATH_TO_DIR_CONTAINING_VC_AND_KEYFILE"
DST_DIR="REPLACE_TARGET_DIR"

VC_NAME="REPLACE_CONTAINER.vc"
KEY_NAME="REPLACE_keyfile.bin"

echo "Ensure ${VC_NAME} is dismounted on BOTH hosts before continuing."
read -r -p "Type YES if both sides are unmounted: " ok
[[ "${ok}" == "YES" ]] || exit 1

rsync -avP --checksum \
  "${REMOTE_USER}@${SOURCE_HOST}:${SRC_DIR}/${VC_NAME}" \
  "${REMOTE_USER}@${SOURCE_HOST}:${SRC_DIR}/${KEY_NAME}" \
  "${REMOTE_USER}@${TARGET_HOST}:${DST_DIR}/"

echo "Optional: sha256sum on source and target to verify."
