#!/usr/bin/env bash
# Deploy the site to Cloudflare Pages.
#
# Why this exists instead of `wrangler pages deploy .`:
#
# Cloudflare Pages pins Cache-Control on .css, .js and .woff2 to
# `public, max-age=14400, must-revalidate` and IGNORES _headers for those paths
# (verified 2026-10-20: a rule for /assets/css/* and even one for the exact file
# both came back as 14400; the /assets/img/* rule below does work, so it is
# extension-based, not a path-matching problem). A stylesheet change therefore
# takes up to four hours to reach anyone who has visited before — including
# whoever is verifying the deploy, which is how a stale sheet reads as "my fix
# did not work".
#
# So the stylesheet and script URLs are fingerprinted with a content hash on the
# way out. The repo keeps plain URLs; only the uploaded copy is rewritten. Change
# site.css, deploy, and every visitor gets the new file immediately, while the
# old URL stays valid for whoever is mid-session.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-/tmp/dist-deploy}"
PROJECT="${PROJECT:-danielspina-info}"
BRANCH="${BRANCH:-main}"

rm -rf "$OUT"
mkdir -p "$OUT"
rsync -a \
  --exclude='.git' --exclude='.github' --exclude='scripts' --exclude='dist' \
  --exclude='README.md' --exclude='.gitignore' --exclude='.wrangler' \
  "$ROOT/" "$OUT/"

python3 - "$ROOT" "$OUT" <<'PY'
import hashlib, os, sys
root, out = sys.argv[1], sys.argv[2]

def digest(rel):
    with open(os.path.join(root, rel), 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:10]

css_hash, js_hash = digest('assets/css/site.css'), digest('assets/js/site.js')
subs = [('/assets/css/site.css', css_hash), ('/assets/js/site.js', js_hash)]
touched = 0
for dirpath, _dirs, files in os.walk(out):
    for name in files:
        if not name.endswith('.html'):
            continue
        path = os.path.join(dirpath, name)
        with open(path, encoding='utf-8') as fh:
            html = fh.read()
        new = html
        for url, fingerprint in subs:
            new = new.replace(url + '"', url + '?v=' + fingerprint + '"')
        if new != html:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(new)
            touched += 1
print('fingerprinted %d pages (css %s, js %s)' % (touched, css_hash, js_hash))
PY

cd "$ROOT"
npx --yes wrangler pages deploy "$OUT" \
  --project-name="$PROJECT" --branch="$BRANCH" --commit-dirty=true
