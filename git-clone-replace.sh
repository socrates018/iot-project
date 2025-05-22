#!/bin/bash
# Clones the iot-project repo into ~/iot-project, replacing any existing directory

set -e

REPO_URL="https://github.com/socrates018/iot-project"
TARGET_DIR="$HOME/iot-project"

TMP_DIR=$(mktemp -d)

echo "Cloning $REPO_URL into $TMP_DIR..."
git clone "$REPO_URL" "$TMP_DIR"

echo "Removing local directory $TARGET_DIR..."
rm -rf "$TARGET_DIR"

echo "Moving cloned repo to $TARGET_DIR..."
mv "$TMP_DIR" "$TARGET_DIR"

echo "Done."
