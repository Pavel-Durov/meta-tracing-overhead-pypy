#!/bin/bash

set -e

DIST=$1

if [ -z "$DIST" ]; then
    DIST="$HOME/tools/pypy"
fi

# Check if PyPy already exists at the target location
if [ -d "$DIST" ] && [ -f "$DIST/bin/pypy3" ]; then
    echo "PyPy already exists at $DIST"
    exit 0
fi

# Download PyPy from the official website
curl https://downloads.python.org/pypy/pypy3.11-v7.3.20-linux64.tar.bz2 -o /tmp/pypy3.11-v7.3.20-linux64.tar.bz2

# Extract the archive
tar -xjf /tmp/pypy3.11-v7.3.20-linux64.tar.bz2

# Move the extracted directory to the desired location
mv pypy3.11-v7.3.20-linux64 $DIST
chmod +x $DIST/bin/pypy3


# Add PyPy to PATH if not already present
if ! grep -q "$DIST/bin" ~/.bashrc; then
    echo "export PATH=\"$DIST/bin:\$PATH\"" >> ~/.bashrc
    echo "Added PyPy to ~/.bashrc"
else
    echo "PyPy already in ~/.bashrc"
fi