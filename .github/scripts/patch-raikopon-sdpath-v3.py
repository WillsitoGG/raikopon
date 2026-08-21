#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

UPSTREAM_SHA256 = "f790c1d81abf21af6d02cb5b350e254784349695688714a21846fff46eac4b33"
OUTPUT_SHA256 = "81ec7aa5b73f347f9cb80d7899445b0cde51d693164d81c5529e1b674ab83638"
OLD = b"sdmc:/switch/azahar/\x00"
NEW = b"sdmc:/switch/raikopon/\x00"
EXPECTED_OFFSET = 0x13308B0
TEXT_END = 0x1213000

# v3 changes ONLY the compiled default user-root literal. No user_dir.txt indirection,
# no ROM-directory literal patch, no argv/direct-launch code patch, no log-path patch.
PRESERVE = [
    b"sdmc:/switch/azahar/user_dir.txt\x00",
    b"sdmc:/switch/azahar/roms/\x00",
    b"sdmc:/switch/azahar/dynarmic_jit.log\x00",
    b"sdmc:/switch/azahar/update_staging_debug.log\x00",
    b"sdmc:/switch/azahar/gpu_frame_log.log\x00",
    b"ROM argument '{}' is not a loadable 3DS title\x00",
    b"ResolveRomPath\x00",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: patch-raikopon-sdpath-v3.py INPUT_NRO OUTPUT_NRO REPORT_JSON", file=sys.stderr)
        return 2

    src, dst, report_path = map(Path, sys.argv[1:])
    original = src.read_bytes()

    if original[0x10:0x14] != b"NRO0":
        raise RuntimeError("Input is not an NRO")
    if sha256(original) != UPSTREAM_SHA256:
        raise RuntimeError("Input is not the exact official Raikopon v2.5.0 release NRO")
    if original.count(OLD) != 1:
        raise RuntimeError(f"Expected exactly one default user-root literal; found {original.count(OLD)}")

    pos = original.index(OLD)
    if pos != EXPECTED_OFFSET:
        raise RuntimeError(f"Unexpected default user-root offset: 0x{pos:X}")

    growth = len(NEW) - len(OLD)
    if growth != 2:
        raise RuntimeError(f"Unexpected growth: {growth}")
    padding = original[pos + len(OLD):pos + len(OLD) + growth]
    if padding != b"\x00" * growth:
        raise RuntimeError("Required zero padding is not present after default user-root literal")

    for marker in PRESERVE:
        if marker not in original:
            raise RuntimeError(f"Expected upstream marker missing: {marker!r}")

    patched = bytearray(original)
    patched[pos:pos + len(NEW)] = NEW
    output = bytes(patched)

    if len(output) != len(original):
        raise RuntimeError("Output size changed")
    if output[0x10:0x14] != b"NRO0":
        raise RuntimeError("Output lost NRO0")
    if OLD in output:
        raise RuntimeError("Old default user-root literal remains")
    if output.count(NEW) != 1:
        raise RuntimeError("New default user-root literal count is not exactly one")

    # Strongest forwarder guard available without hardware: the entire executable/text segment
    # must remain byte-for-byte identical to the official release. v3 changes only RO data.
    if output[:TEXT_END] != original[:TEXT_END]:
        raise RuntimeError("Executable/text segment changed")

    for marker in PRESERVE:
        if marker not in output:
            raise RuntimeError(f"Preserved upstream marker changed: {marker!r}")

    # v3 must not introduce a Raikopon ROM-directory literal or Raikopon user_dir pointer.
    if b"sdmc:/switch/raikopon/roms/\x00" in output:
        raise RuntimeError("ROM-directory literal was unexpectedly patched")
    if b"sdmc:/switch/raikopon/user_dir.txt\x00" in output:
        raise RuntimeError("user_dir.txt indirection was unexpectedly patched")

    changed = [i for i, (a, b) in enumerate(zip(original, output)) if a != b]
    allowed = set(range(pos, pos + len(NEW)))
    unexpected = [i for i in changed if i not in allowed]
    if unexpected:
        raise RuntimeError(f"Unexpected binary deltas outside default root literal: {unexpected[:16]}")

    out_sha = sha256(output)
    if out_sha != OUTPUT_SHA256:
        raise RuntimeError(f"Unexpected v3 output SHA-256: {out_sha}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(output)

    report = {
        "upstream": "Raibatsu/raikopon v2.5.0 official release asset raikopon.nro",
        "input_sha256": UPSTREAM_SHA256,
        "output_sha256": out_sha,
        "input_size": len(original),
        "output_size": len(output),
        "patched_offset": f"0x{pos:X}",
        "old": OLD[:-1].decode("ascii"),
        "new": NEW[:-1].decode("ascii"),
        "changed_byte_positions_count": len(changed),
        "only_default_user_root_literal_changed": True,
        "entire_executable_text_segment_byte_identical_to_upstream": True,
        "argv_and_direct_launch_code_byte_identical_to_upstream": True,
        "rom_directory_literal_byte_identical_to_upstream": True,
        "user_dir_pointer_literal_byte_identical_to_upstream": True,
        "user_dir_pointer_required": False,
        "physical_switch_forwarder_test_performed": False,
        "nro_magic_valid": True,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
