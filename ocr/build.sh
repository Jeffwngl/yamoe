#!/usr/bin/env bash

echo "Setting up..."

os="$(uname -s)"

case "$os" in
    Darwin)
        reqs="requirements-darwin.txt"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        reqs="requirements-windows.txt"
        ;;
    *)
        echo "Unsupported operating system: $os"
        exit 1
        ;;
esac

cd "$(dirname "$0")"

python3 -m venv .venv

if [[ "$os" == MINGW* || "$os" == MSYS* || "$os" == CYGWIN* ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r "$reqs"

if [[ "$os" == "Darwin" ]]; then
    echo "Compiling VisionKit helper..."

    if ! command -v swiftc >/dev/null 2>&1; then
        echo "Swift compiler not found. Install Xcode Command Line Tools."
        exit 1
    fi

    swiftc visionkit_helper.swift -o visionkit_helper
fi

echo "Backend setup complete."