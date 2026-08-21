#!/usr/bin/env bash
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
OUT="${OUT:-$ROOT/raikopon-v3-output}"
WORK="${WORK:-/tmp/raikopon-v3}"
OFFICIAL_SHA="f790c1d81abf21af6d02cb5b350e254784349695688714a21846fff46eac4b33"
FINAL_SHA="81ec7aa5b73f347f9cb80d7899445b0cde51d693164d81c5529e1b674ab83638"
PATCHER_BLOB="ffd56106f3096eaf01aa1c13c96f94d17f7be101"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$WORK"

test "$(git hash-object .github/scripts/patch-raikopon-sdpath-v3.py)" = "$PATCHER_BLOB"

python3 - "$WORK/official.nro" <<'PY'
import hashlib, json, pathlib, sys, urllib.request
out=pathlib.Path(sys.argv[1])
expected='f790c1d81abf21af6d02cb5b350e254784349695688714a21846fff46eac4b33'
req=urllib.request.Request('https://api.github.com/repos/Raibatsu/raikopon/releases?per_page=50',headers={'User-Agent':'willsito-raikopon-builder'})
with urllib.request.urlopen(req) as r: releases=json.load(r)
rel=next((x for x in releases if str(x.get('tag_name','')) in {'v2.5.0','2.5.0'}),None)
if rel is None: raise SystemExit('Official Raikopon v2.5.0 release not found')
assets=rel.get('assets',[])
asset=next((a for a in assets if a.get('name','').lower()=='raikopon.nro'),None)
if asset is None: raise SystemExit('Official raikopon.nro asset not found')
q=urllib.request.Request(asset['browser_download_url'],headers={'User-Agent':'willsito-raikopon-builder'})
with urllib.request.urlopen(q) as src, out.open('wb') as dst:
    while True:
        b=src.read(1024*1024)
        if not b: break
        dst.write(b)
actual=hashlib.sha256(out.read_bytes()).hexdigest()
if actual != expected: raise SystemExit(f'Official SHA mismatch: {actual}')
pathlib.Path(str(out)+'.release.txt').write_text(
    f"tag={rel.get('tag_name')}\nname={rel.get('name')}\nasset={asset.get('name')}\npublished_at={rel.get('published_at')}\n")
PY

test "$(sha256sum "$WORK/official.nro" | awk '{print $1}')" = "$OFFICIAL_SHA"
python3 .github/scripts/patch-raikopon-sdpath-v3.py \
  "$WORK/official.nro" "$OUT/raikopon.nro" "$OUT/PATCH_REPORT.json"
test "$(sha256sum "$OUT/raikopon.nro" | awk '{print $1}')" = "$FINAL_SHA"
cmp -s <(head -c $((0x1213000)) "$WORK/official.nro") <(head -c $((0x1213000)) "$OUT/raikopon.nro")
cp "$WORK/official.nro.release.txt" "$OUT/OFFICIAL_RELEASE.txt"
printf '%s  raikopon-official-v2.5.0.nro\n' "$OFFICIAL_SHA" > "$OUT/OFFICIAL_SHA256SUMS.txt"
printf '%s  raikopon.nro\n' "$FINAL_SHA" > "$OUT/SHA256SUMS.txt"
cat > "$OUT/PROVENANCE.txt" <<EOF
Raikopon v2.5.0 – Raikopon SD Path_v3
Official NRO SHA-256: $OFFICIAL_SHA
Final v3 NRO SHA-256: $FINAL_SHA
Exact patcher blob: $PATCHER_BLOB
Change: only compiled default user root sdmc:/switch/azahar/ -> sdmc:/switch/raikopon/
Executable/text segment: byte-for-byte official
argv/direct-forwarder code: byte-for-byte official
ROM-directory literal: byte-for-byte official
user_dir.txt pointer literal: byte-for-byte official
Hardware validation: final v3 was manually tested by Willsito on a real Nintendo Switch.
EOF
cat "$OUT/SHA256SUMS.txt"
