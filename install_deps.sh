#!/bin/bash

sudo apt update
sudo apt install -y clang-tidy cppcheck openjdk-17-jdk android-sdk android-tools-adb android-tools-fastboot

sudo snap install android-studio --classic

echo "Dependencies installed (linting + Java + Android SDK + Android Studio)"