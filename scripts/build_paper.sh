#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p output/pdf
tectonic -o output/pdf paper/main.tex
mv output/pdf/main.pdf output/pdf/undoscope-paper.pdf
