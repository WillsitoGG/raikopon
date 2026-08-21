# Raikopon – WillsitoGG tuning

This fork keeps `Raibatsu/raikopon` clean on `master` and stores WillsitoGG-specific binary tuning work on `willsito-tuning`.

## Branch model

- `master`: exact upstream tracking branch. No tuning files or patched NROs belong here.
- `willsito-tuning`: permanent tuning branch with the reproducible NRO patcher, validation, release notes and historical archive.

## Current tuning

**Raikopon v2.5.0 – Raikopon SD Path_v3**

The tuning starts from the exact official Raikopon v2.5.0 `raikopon.nro` and changes only the compiled default user-data root:

`sdmc:/switch/azahar/` → `sdmc:/switch/raikopon/`

Current identities:

- Official v2.5.0 NRO SHA-256: `f790c1d81abf21af6d02cb5b350e254784349695688714a21846fff46eac4b33`
- Current patched NRO SHA-256: `81ec7aa5b73f347f9cb80d7899445b0cde51d693164d81c5529e1b674ab83638`
- Exact v3 patcher Git blob: `ffd56106f3096eaf01aa1c13c96f94d17f7be101`

The patch changes only 9 byte positions in the single default user-root literal. The executable/text segment, `argv` handling, direct-launch code, ROM-directory literal and `user_dir.txt` pointer literal remain byte-for-byte official.

The v3 build was manually tested on a real Nintendo Switch, including the `/switch/raikopon/` user-data location and direct game launching through forwarders.

## Historical revisions

- `Raikopon v2.5.0 – Raikopon SD Path_v1`
- `Raikopon v2.5.0 – Raikopon SD Path_v2`

Their exact patchers and published SHA-256 identities are preserved under `Archive/`. Historical NROs may only be added if a deterministic reconstruction matches the original published SHA-256 exactly.

## Release policy

Only v3 should remain visible under Releases. The user-facing asset is `raikopon.nro`. Superseded final revisions belong under `Archive/`; failed or experimental CoverM work is not part of the historical final-release archive.
