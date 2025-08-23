#!/bin/bash

sudo apt update
sudo apt install -y clang-tidy cppcheck

echo "Linting dependencies installed"