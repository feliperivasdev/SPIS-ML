#!/bin/bash
set -e
cd dashboard
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo "Build complete"
