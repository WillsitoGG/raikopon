# AGENTS.md

## Branches

- Keep `master` identical to `Raibatsu/raikopon` unless explicitly synchronizing with upstream.
- Keep all WillsitoGG binary tuning, archive, validation and release material on `willsito-tuning`.

## Current v3 identity

The current tuning is a deterministic binary patch of the exact official Raikopon v2.5.0 NRO.

- Official NRO SHA-256: `f790c1d81abf21af6d02cb5b350e254784349695688714a21846fff46eac4b33`
- Patched v3 NRO SHA-256: `81ec7aa5b73f347f9cb80d7899445b0cde51d693164d81c5529e1b674ab83638`
- Exact patcher: `.github/scripts/patch-raikopon-sdpath-v3.py`
- Exact patcher Git blob: `ffd56106f3096eaf01aa1c13c96f94d17f7be101`

Do not broaden the v3 patch. It must only change the single compiled default user-root literal from `sdmc:/switch/azahar/` to `sdmc:/switch/raikopon/`.

## Forwarder preservation

The following must remain byte-for-byte upstream in v3:

- the entire executable/text segment,
- `argc/argv` parsing and direct launch code,
- ROM-directory handling,
- the `sdmc:/switch/azahar/roms/` literal,
- the `sdmc:/switch/azahar/user_dir.txt` pointer literal.

Do not reintroduce the v2 `user_dir.txt` workaround into v3.

## Historical archive

Published historical identities:

- v1 NRO SHA-256: `9512fbe1a51c365d79fc0f46895445965ed06eb87394b9f4ef6209745fbadd55`
- v2 NRO SHA-256: `4f1f6bc0411285c336ef62ad1ee9815aff9a1bc31e08c35a3429fb661c97f4b5`

The exact historical patchers must be preserved. A reconstructed historical NRO may be archived only when its SHA-256 exactly equals the corresponding published identity. Otherwise preserve documentation/patchers/hashes only and state that the exact binary is unavailable.

## Hardware validation

The current v3 was manually tested by Willsito on a real Nintendo Switch, including direct forwarders and the `/switch/raikopon/` user-data location. Automated reports do not replace that hardware validation.

## Releases

Only the current v3 final tuning should remain visible in Releases. The release asset should be only `raikopon.nro` unless explicitly requested otherwise.

## Cleanliness

Do not keep temporary workflows, trigger files, logs, CoverM experiments or failed/discarded builds in the permanent tuning branch.
