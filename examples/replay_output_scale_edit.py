"""Verify or replay the Pilot 176 binary16 scale edit on the exact Pilot 024 GGUF."""

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import stat
import struct


HELPER = Path(__file__).resolve().with_name("replay_output_row_edit.py")
HELPER_SHA256 = "ee8c23279d1f10537371e58cfaa9850556530a07322314ee5813ece5820ecabd"
CAPSULE_SHA256 = "099b28ee25a61fd26d35a76dc91c7a363c54fbe700086c517c0b2b0772e34aca"
FIELD_OFFSET = {"d": 0, "dmin": 2}
BLOCK_BYTES = 144


def require(condition, message):
    if not condition:
        raise ValueError(message)


def replay_helpers():
    # Git may convert line endings in Windows checkouts.
    raw = HELPER.read_bytes().replace(b"\r\n", b"\n")
    require(sha256(raw).hexdigest() == HELPER_SHA256, "Historical GGUF replay helper SHA-256 differs")
    scope = {"__name__": "pinned_gguf_replay", "__file__": str(HELPER)}
    exec(compile(raw, str(HELPER), "exec"), scope)
    return scope


def binary16(encoded):
    require(isinstance(encoded, str) and len(encoded) == 4, "Expected two binary16 bytes")
    raw = bytes.fromhex(encoded)
    require(raw.hex() == encoded, "Expected canonical lowercase binary16 bytes")
    value, = struct.unpack("<e", raw)
    require(math.isfinite(value) and value > 0, "Q4_K scale fields must be positive and finite")
    return raw


def row_fields(fields, row_bytes):
    require(isinstance(fields, list) and fields, "Expected declared binary16 scale fields")
    changes = []
    last_offset = -1
    for entry in fields:
        require(isinstance(entry, dict) and set(entry) == {"block", "field", "before", "after"}
                and type(entry["block"]) is int and 0 <= entry["block"] < row_bytes // BLOCK_BYTES
                and isinstance(entry["field"], str) and entry["field"] in FIELD_OFFSET,
                "Expected an in-range Q4_K d or dmin field")
        offset = entry["block"] * BLOCK_BYTES + FIELD_OFFSET[entry["field"]]
        before, after = (binary16(entry[k]) for k in ("before", "after"))
        require(offset > last_offset and before != after, "Expected unique, ordered, changed binary16 fields")
        changes.append((offset, before, after))
        last_offset = offset
    return tuple(changes)


def load_capsule(helpers):
    path = helpers["EVIDENCE"] / "direct-closure-pilot-176-row-patch.json"
    patch = json.loads(path.read_bytes())
    canonical = json.dumps(patch, sort_keys=True, separators=(",", ":")).encode("ascii")
    require(sha256(canonical).hexdigest() == CAPSULE_SHA256 and patch["pilot"] == 176
            and patch["schema"] == "public-direct-output-multirow-q4k-binary16-patch-v1",
            "Pilot 176 scale capsule SHA-256 or schema differs")

    tensor = patch["tensor"]
    width, count = tensor["dimensions"]
    require(tensor["name"] == "output.weight" and tensor["ggml_type"] == 12
            and tensor["quantization"] == "Q4_K" and width > 0 and width % 256 == 0,
            "Expected a packed Q4_K output tensor")
    row_bytes = width // 256 * BLOCK_BYTES
    require(tensor["bytes"] == count * row_bytes
            and 0 <= tensor["offset"] < tensor["offset"] + tensor["bytes"] <= patch["checkpoint_bytes"],
            "Patch tensor extent differs")
    rows = patch["rows"]
    require([row["token_id"] for row in rows] == [351, 357, 414, 417],
            "Expected the four pinned rows in physical order")
    changes = []
    for row in rows:
        require(row["token_id"] < count and row["bytes"] == row_bytes
                and row["offset"] == tensor["offset"] + row["token_id"] * row_bytes,
                "Patch tensor and row extents disagree")
        changes.append(row_fields(row["changed_fields"], row_bytes))
    require(sum(map(len, changes)) == patch["changed_binary16_fields"]
            and sum(a != b for row in changes for _, before, after in row
                    for a, b in zip(before, after, strict=True)) == patch["changed_bytes"],
            "Total binary16 field or changed-byte count differs")
    return patch, tuple(changes)


def checked_byte_masks(parent, patch, changes, helpers):
    # The streaming replay independently checks the parent row and whole-file
    # hashes, so the masks also bind to the same bytes when the file is reopened.
    masks = []
    with parent.open("rb") as source:
        info = os.fstat(source.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size == patch["checkpoint_bytes"],
                "Parent must be a regular file of the pinned size")
        for row, fields in helpers["row_patches"](patch, changes):
            source.seek(row["offset"])
            original = helpers["read_exact"](source, row["bytes"])
            require(sha256(original).hexdigest() == row["parent_sha256"], "Parent row SHA-256 differs")
            byte_masks = []
            for offset, before, after in fields:
                require(original[offset:offset + 2] == before, "Declared parent binary16 scale bytes differ")
                byte_masks.extend((offset + index, a ^ b) for index, (a, b) in enumerate(zip(before, after, strict=True))
                                  if a != b)
            masks.append(tuple(byte_masks))
    return tuple(masks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True, help="Exact Pilot 024 parent GGUF")
    parser.add_argument("--output", type=Path, help="Optional fresh GGUF path on a hard-link-capable filesystem")
    args = parser.parse_args()
    try:
        helpers = replay_helpers()
        patch, fields = load_capsule(helpers)
        masks = checked_byte_masks(args.parent, patch, fields, helpers)
        helpers["replay"](args.parent, args.output, patch, masks)
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"Replay failed. {error}\n")
    print(json.dumps(dict(status="WRITTEN_AND_VERIFIED" if args.output else "VERIFIED_ONLY",
                          parent_sha256=patch["parent_sha256"], candidate_sha256=patch["candidate_sha256"],
                          changed_binary16_fields=patch["changed_binary16_fields"], changed_bytes=patch["changed_bytes"],
                          rows=[dict(token_id=row["token_id"], parent_row_sha256=row["parent_sha256"],
                                     candidate_row_sha256=row["candidate_sha256"], changed_bytes=len(changes))
                                for row, changes in helpers["row_patches"](patch, masks)]), indent=2))


if __name__ == "__main__":
    main()
