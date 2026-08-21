# Raikopon v2.5.0 – Raikopon SD Path_v3

Changes the compiled default Nintendo Switch user-data root from:

`sdmc:/switch/azahar/`

to:

`sdmc:/switch/raikopon/`

The patch is deliberately minimal:

- only one embedded default user-root literal is modified,
- file size is unchanged,
- only 9 byte positions differ,
- the complete executable/text segment is byte-for-byte official,
- `argv` and direct-forwarder handling are unchanged,
- the default ROM-directory literal is unchanged,
- no `user_dir.txt` workaround is required.

Official v2.5.0 SHA-256:

`f790c1d81abf21af6d02cb5b350e254784349695688714a21846fff46eac4b33`

Final v3 SHA-256:

`81ec7aa5b73f347f9cb80d7899445b0cde51d693164d81c5529e1b674ab83638`

This final v3 build was manually tested on a real Nintendo Switch. The `/switch/raikopon/` user-data location and direct game launching through forwarders were both verified.
