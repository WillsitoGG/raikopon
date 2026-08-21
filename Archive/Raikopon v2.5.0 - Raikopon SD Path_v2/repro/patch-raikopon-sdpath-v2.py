#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

UPSTREAM_SHA256 = "f790c1d81abf21af6d02cb5b350e254784349695688714a21846fff46eac4b33"
OLD_PREFIX = b"sdmc:/switch/azahar"
NEW_PREFIX = b"sdmc:/switch/raikopon"

# v2 deliberately does NOT patch the default user-dir literal or the default ROM-directory
# literal. The official user_dir.txt mechanism redirects the runtime user-data root instead.
# This keeps all ROM/argv-related literals and direct-launch code byte-for-byte upstream.
REPLACEMENTS: list[tuple[bytes, bytes, str]] = [
    (
        b"sdmc:/switch/azahar/dynarmic_jit.log",
        b"sdmc:/switch/raikopon/dynarmic_jit.log",
        "Dynarmic JIT log",
    ),
    (
        b"sdmc:/switch/azahar/update_staging_debug.log",
        b"sdmc:/switch/raikopon/update_staging_debug.log",
        "Updater staging debug log",
    ),
    (
        b"sdmc:/switch/azahar/user_dir.txt",
        b"sdmc:/switch/raikopon/user_dir.txt",
        "user_dir.txt lookup path",
    ),
    (
        b"sdmc:/switch/azahar/gpu_frame_log.log",
        b"sdmc:/switch/raikopon/gpu_frame_log.log",
        "GPU frame log",
    ),
]

# Static-analysis anchors for the exact official v2.5.0 NRO.
# IsLoadableRom probes the supplied ROM path. ResolveRomPath/direct-launch checks whether an
# argument exists, calls IsLoadableRom, and copies the supplied string directly when valid.
# Both regions must remain byte-for-byte identical to upstream.
CODE_REGIONS = {
    "IsLoadableRom": (0x5342C0, 0x5344B4),
    "ResolveRomPath_and_direct_launch": (0x537260, 0x539044),
}

# These markers are intentionally kept exactly as official. In particular, ROM-directory
# handling is not patched in v2.
PRESERVE_MARKERS = [
    b"sdmc:/switch/azahar/\x00",
    b"sdmc:/switch/azahar/roms/\x00",
    b"ROM argument '{}' is not a loadable 3DS title\x00",
    b"ResolveRomPath\x00",
    b"roms/\x00",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_all(data: bytes, needle: bytes) -> list[int]:
    out: list[int] = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return out
        out.append(pos)
        start = pos + 1


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: patch-raikopon-sdpath-v2.py INPUT_NRO OUTPUT_NRO REPORT_JSON", file=sys.stderr)
        return 2

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    report_path = Path(sys.argv[3])

    original = src.read_bytes()
    if len(original) < 0x14 or original[0x10:0x14] != b"NRO0":
        raise RuntimeError("Input does not look like a Nintendo Switch NRO (missing NRO0 at 0x10)")

    input_sha = sha256(original)
    if input_sha != UPSTREAM_SHA256:
        raise RuntimeError(f"Unexpected upstream NRO SHA-256: {input_sha}")

    old_prefix_offsets = find_all(original, OLD_PREFIX)
    if len(old_prefix_offsets) != 11:
        raise RuntimeError(
            f"Expected 11 sdmc:/switch/azahar occurrences in official v2.5.0; found {len(old_prefix_offsets)}"
        )

    for marker in PRESERVE_MARKERS:
        if marker not in original:
            raise RuntimeError(f"Expected upstream preserve marker missing: {marker!r}")

    region_hashes_before = {
        name: sha256(original[start:end]) for name, (start, end) in CODE_REGIONS.items()
    }

    patched = bytearray(original)
    allowed_ranges: list[tuple[int, int]] = []
    applied: list[dict[str, object]] = []

    for old, new, label in REPLACEMENTS:
        positions = find_all(original, old + b"\x00")
        if len(positions) != 1:
            raise RuntimeError(f"Expected exactly one {label} literal; found {len(positions)}")

        pos = positions[0]
        growth = len(new) - len(old)
        if growth < 0:
            raise RuntimeError(f"Unexpected shrink for {label}")

        old_end = pos + len(old) + 1
        padding = original[old_end : old_end + growth]
        if padding != b"\x00" * growth:
            raise RuntimeError(
                f"Unsafe growth for {label} at 0x{pos:X}: expected {growth} zero padding bytes"
            )

        replacement = new + b"\x00"
        patched[pos : pos + len(replacement)] = replacement
        allowed_ranges.append((pos, pos + len(replacement)))
        applied.append(
            {
                "label": label,
                "offset": f"0x{pos:X}",
                "old": old.decode("ascii"),
                "new": new.decode("ascii"),
                "growth_bytes": growth,
            }
        )

    output = bytes(patched)
    if len(output) != len(original):
        raise RuntimeError("Patched NRO changed file size")
    if output[0x10:0x14] != b"NRO0":
        raise RuntimeError("Patched NRO lost NRO0 magic")

    for old, new, label in REPLACEMENTS:
        if old + b"\x00" in output:
            raise RuntimeError(f"Old path remains after patch: {label}")
        if new + b"\x00" not in output:
            raise RuntimeError(f"New path missing after patch: {label}")

    diff_positions = [i for i, (a, b) in enumerate(zip(original, output)) if a != b]

    def is_allowed(i: int) -> bool:
        return any(start <= i < end for start, end in allowed_ranges)

    unexpected = [i for i in diff_positions if not is_allowed(i)]
    if unexpected:
        preview = ", ".join(f"0x{i:X}" for i in unexpected[:20])
        raise RuntimeError(f"Binary changed outside approved internal-data literals: {preview}")

    # Critical forwarder guards: keep all ROM/argv-related constants and code official.
    for marker in PRESERVE_MARKERS:
        if marker not in output:
            raise RuntimeError(f"Preserved ROM/argv marker changed: {marker!r}")
    if b"sdmc:/switch/raikopon/roms/\x00" in output:
        raise RuntimeError("v2 must not rewrite the default ROM-directory literal")

    region_hashes_after = {
        name: sha256(output[start:end]) for name, (start, end) in CODE_REGIONS.items()
    }
    if region_hashes_after != region_hashes_before:
        raise RuntimeError("IsLoadableRom or ResolveRomPath/direct-launch code changed")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(output)

    report = {
        "upstream": "Raibatsu/raikopon v2.5.0 official release asset raikopon.nro",
        "purpose": "Move Raikopon user-data selection and absolute internal debug logs to switch/raikopon while leaving ROM/argv handling exactly upstream",
        "input_size": len(original),
        "output_size": len(output),
        "input_sha256": input_sha,
        "output_sha256": sha256(output),
        "patched_literals": applied,
        "changed_byte_positions_count": len(diff_positions),
        "binary_delta_confined_to_internal_data_literals": True,
        "default_user_dir_literal_preserved_from_upstream": True,
        "default_rom_dir_literal_preserved_from_upstream": True,
        "argv_direct_launch_regions_byte_identical": True,
        "code_region_sha256": region_hashes_after,
        "old_prefix_occurrences_before": len(old_prefix_offsets),
        "old_prefix_occurrences_after": len(find_all(output, OLD_PREFIX)),
        "new_prefix_occurrences_after": len(find_all(output, NEW_PREFIX)),
        "nro_magic_valid": True,
        "physical_switch_forwarder_test_performed": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
