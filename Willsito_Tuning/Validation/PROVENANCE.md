# Raikopon v2.5.0 – Raikopon SD Path_v3

- Upstream Release: `Raibatsu/raikopon v2.5.0`.
- Upstream NRO SHA-256: `f790c1d81abf21af6d02cb5b350e254784349695688714a21846fff46eac4b33`.
- Patched NRO SHA-256: `81ec7aa5b73f347f9cb80d7899445b0cde51d693164d81c5529e1b674ab83638`.
- Patch scope: one compiled default user-root literal only: `sdmc:/switch/azahar/` → `sdmc:/switch/raikopon/`.
- Changed byte positions: `9`.
- Output size: identical to upstream (`45,934,357` bytes).
- Executable/text segment: byte-identical to upstream.
- argv/direct-forwarder code: byte-identical to upstream.
- Default ROM-directory literal: byte-identical to upstream.
- `user_dir.txt` pointer literal: byte-identical to upstream.
- `user_dir.txt` required by this tune: no.
- Physical Switch forwarder test: unavailable in CI; this record documents reproducible binary validation only.
