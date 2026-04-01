#!/bin/bash
set -euo pipefail

python3 scripts/07_render_html.py

mkdir -p docs/data
rm -rf docs/data/daodejing docs/data/nanhua
cp -R data/daodejing docs/data/
cp -R data/nanhua docs/data/
cp data/site_stats.json docs/data/site_stats.json
