#!/usr/bin/env bash

set -e

echo "==> Updating project..."

git pull origin main

echo "==> Re-running installer..."
bash install.sh

echo "==> Done"