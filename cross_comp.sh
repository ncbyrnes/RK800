#!/bin/bash
set -e
TARGET_DIR="/opt/cross/android-ndk-r28c-linux"
NDK_URL="https://dl.google.com/android/repository/android-ndk-r28c-linux.zip"
NDK_ZIP="android-ndk-r28c-linux.zip"

sudo mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

echo "Downloading Android NDK stuff :D"
wget -q --show-progress "$NDK_URL" -O "$NDK_ZIP"

echo "Extracting"
sudo apt-get update -qq
sudo apt-get install -y unzip
unzip -q "$NDK_ZIP"

rm "$NDK_ZIP"

echo "Done"