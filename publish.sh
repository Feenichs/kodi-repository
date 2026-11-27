#!/bin/sh
# Publishes dist/ (from build.py) as the branch gh-pages, as a single commit
# without history, so old zips do not pile up in the repository.
set -e
cd "$(dirname "$0")"
test -f dist/addons.xml || { echo "run build.py first" >&2; exit 1; }
url=$(git remote get-url origin)
cd dist
rm -rf .git
git init -q -b gh-pages
git add -A
git commit -q -m "Repository as of $(date -u +%Y-%m-%d)"
git push -q -f "$url" gh-pages
rm -rf .git
echo "published to gh-pages"
