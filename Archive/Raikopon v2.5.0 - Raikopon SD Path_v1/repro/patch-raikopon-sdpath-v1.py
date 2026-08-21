#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

OLD_PREFIX = b"sdmc:/switch/azahar"
NEW_PREFIX = b"sdmc:/switch/raikopon"

# Scope: normal emulator data/runtime filesystem paths only.
# Forwarder argv/game paths are never searched, rewritten, normalized, or redirected.
# The updater developer-test override is deliberately left byte-for-byte upstream because
# it is not part of the emulator user-data/ROM/runtime directory model.
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
        b"sdmc:/switch/azahar/log/\n",
        b"sdmc:/switch/raikopon/log/\n",
        "Embedded runtime log directory line",
    ),
    (
        b"sdmc:/switch/azahar/",
        b"sdmc:/switch/raikopon/",
        "Default user-data directory",
    ),
    (
        b"sdmc:/switch/azahar/user_dir.txt",
        b"sdmc:/switch/raikopon/user_dir.txt",
        "User-directory pointer file",
    ),
    (
        b"sdmc:/switch/azahar/roms/",
        b"sdmc:/switch/raikopon/roms/",
        "Default ROM browser directory",
    ),
    (
        b"sdmc:/switch/azahar/gpu_frame_log.log",
        b"sdmc:/switch/raikopon/gpu_frame_log.log",
        "GPU frame log",
    ),
]

# Four old-prefix occurrences are intentionally retained:
# - three are embedded documentation/help text;
# - one is the updater developer-test URL override, not an emulator data path.
EXPECTED_REMAINING_MARKERS = [
    b"sdmc:/switch/azahar/gpu_frame_log.log and\n# dynarmic_jit.log",
    b"sdmc:/switch/azahar/roms/ when unset.\n# The Raika Azahar",
    b"sdmc:/switch/azahar/user_dir.txt\nroms_dir =",
    b"sdmc:/switch/azahar/update_test_url.txt\x00",
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
        print("usage: patch-raikopon-sdpath-v1.py INPUT_NRO OUTPUT_NRO REPORT_JSON", file=sys.stderr)
        return 2

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    report_path = Path(sys.argv[3])

    original = src.read_bytes()
    if len(original) < 0x14 or original[0x10:0x14] != b"NRO0":
        raise RuntimeError("Input does not look like a Nintendo Switch NRO (missing NRO0 magic at 0x10)")

    old_prefix_offsets = find_all(original, OLD_PREFIX)
    if len(old_prefix_offsets) != 11:
        raise RuntimeError(
            f"Expected 11 embedded sdmc:/switch/azahar references in official v2.5.0; found {len(old_prefix_offsets)}"
        )

    patched = bytearray(original)
    applied: list[dict[str, object]] = []
    allowed_ranges: list[tuple[int, int]] = []

    located: list[tuple[int, bytes, bytes, str]] = []
    for old, new, label in REPLACEMENTS:
        needle = old + b"\x00"
        positions = find_all(original, needle)
        if len(positions) != 1:
            raise RuntimeError(
                f"Expected exactly one NUL-terminated occurrence for {label}: {old!r}; found {len(positions)}"
            )
        located.append((positions[0], old, new, label))

    # Patch in descending offset order. File length is never changed. Any path growth must fit
    # entirely into existing zero padding immediately following the original string.
    for pos, old, new, label in sorted(located, reverse=True):
        old_span = len(old) + 1
        new_span = len(new) + 1
        growth = new_span - old_span
        old_end = pos + old_span

        if growth > 0:
            padding = original[old_end:old_end + growth]
            if len(padding) != growth or any(padding):
                raise RuntimeError(
                    f"Unsafe growth for {label} at 0x{pos:X}: needs {growth} zero padding bytes; "
                    f"following={original[old_end:old_end + max(16, growth)].hex(' ')}"
                )

        replacement = new + b"\x00"
        patched[pos:pos + len(replacement)] = replacement
        allowed_ranges.append((pos, pos + len(replacement)))

        applied.append(
            {
                "offset": f"0x{pos:X}",
                "label": label,
                "old": old.decode("ascii"),
                "new": new.decode("ascii"),
                "growth_bytes": growth,
                "allowed_delta_start": f"0x{pos:X}",
                "allowed_delta_end_exclusive": f"0x{pos + len(replacement):X}",
            }
        )

    patched_bytes = bytes(patched)

    if len(patched_bytes) != len(original):
        raise RuntimeError("Patched NRO changed file size")
    if patched_bytes[0x10:0x14] != b"NRO0":
        raise RuntimeError("Patched file lost NRO0 magic")

    for old, new, label in REPLACEMENTS:
        if old + b"\x00" in patched_bytes:
            raise RuntimeError(f"Old operational data path remains after patch: {label}")
        if new + b"\x00" not in patched_bytes:
            raise RuntimeError(f"New operational data path missing after patch: {label}")

    remaining_old_offsets = find_all(patched_bytes, OLD_PREFIX)
    if len(remaining_old_offsets) != 4:
        raise RuntimeError(
            f"Expected exactly 4 deliberately retained old-prefix references; found {len(remaining_old_offsets)}"
        )
    for marker in EXPECTED_REMAINING_MARKERS:
        if marker not in patched_bytes:
            raise RuntimeError(f"Expected retained marker missing: {marker!r}")

    new_prefix_offsets = find_all(patched_bytes, NEW_PREFIX)
    if len(new_prefix_offsets) != 7:
        raise RuntimeError(f"Expected 7 operational Raikopon data-path references; found {len(new_prefix_offsets)}")

    # Critical forwarder-preservation proof: every changed byte must be confined to one of the
    # seven explicitly allowed embedded path literal spans. Therefore executable code, argv
    # parsing, direct-game launch logic, and all unrelated data remain byte-for-byte upstream.
    diff_positions = [i for i, (a, b) in enumerate(zip(original, patched_bytes)) if a != b]
    if not diff_positions:
        raise RuntimeError("Patch made no changes")

    def in_allowed_range(i: int) -> bool:
        return any(start <= i < end for start, end in allowed_ranges)

    unexpected_diffs = [i for i in diff_positions if not in_allowed_range(i)]
    if unexpected_diffs:
        preview = ", ".join(f"0x{i:X}" for i in unexpected_diffs[:20])
        raise RuntimeError(f"Binary changed outside approved path literals: {preview}")

    # Also prove each approved path span is the only source of delta by comparing the complement.
    for i, (a, b) in enumerate(zip(original, patched_bytes)):
        if not in_allowed_range(i) and a != b:
            raise RuntimeError(f"Unexpected non-path delta at 0x{i:X}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(patched_bytes)

    report = {
        "upstream": "Raibatsu/raikopon v2.5.0 official release asset raikopon.nro",
        "purpose": "Move Raikopon emulator data/runtime paths from sdmc:/switch/azahar to sdmc:/switch/raikopon while preserving direct forwarder argv handling",
        "input_size": len(original),
        "output_size": len(patched_bytes),
        "input_sha256": sha256(original),
        "output_sha256": sha256(patched_bytes),
        "old_prefix_occurrences_before": len(old_prefix_offsets),
        "operational_data_paths_patched": len(applied),
        "new_operational_prefix_occurrences_after": len(new_prefix_offsets),
        "remaining_old_prefix_occurrences_after": len(remaining_old_offsets),
        "remaining_old_prefixes_are_docs_or_updater_test_only": True,
        "applied_replacements": sorted(applied, key=lambda item: int(str(item["offset"]), 16)),
        "changed_byte_positions_count": len(diff_positions),
        "binary_delta_confined_to_approved_path_literals": True,
        "executable_and_argv_logic_byte_identical_to_upstream": True,
        "forwarder_rom_argument_rewriting_added": False,
        "nro_magic_valid": patched_bytes[0x10:0x14] == b"NRO0",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
