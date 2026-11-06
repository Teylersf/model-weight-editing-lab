"""Verify or replay a published mixed Q4_K edit on the exact Pilot 024 GGUF."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import struct


SCALE_HELPER = Path(__file__).resolve().with_name("replay_output_scale_edit.py")
SCALE_HELPER_SHA256 = "e6ae7c2d5ef81d4506351a35150c8750c63e7db1953a21589334367a66b07083"
CAPSULES = {
    194: ("dd7699cd82329afdb638c3b32b85ca00922a65e9b5abb1b8cf951e11ca167df8", 158, 21, 1, 0),
    209: ("4f746569230c4a7e7f3a7002ccfaceb1f466c2c5f70d2b3f0923d0f44a897bc2", 158, 3713, 2, 0),
    217: ("579b6fb2e4e5dca322f2af62efe3830121b5eb114554997b73de02228fd5dde2", 157, 3716, 2, 0),
    241: ("149470552bb4bf2694d90f75870b4c262ae80b208bb191df9c4309f1f5eb9220", 159, 21, 1, 3),
    243: ("78460897d006622c79a8634bc040f7ee1c9d784384dd780fab5b9f1e516a5333", 153, 21, 1, 3),
}
GROUP_FIELD_INDEX = {"scale": 0, "minimum": 1}
GROUP_COUNTS = ("changed_group_fields", "changed_group_metadata_bytes", "changed_group_metadata_bits", "changed_bits")
PARENT_SHA256 = "674c1e84a2adbf0232b6bb3d4d24a4d00f7c60b109d665f3fe5c88a484589db3"
CHECKPOINT_BYTES = 11674147744
ROW_BYTES = 2880
TOKENS = (351, 357, 414, 417)
TENSOR = dict(name="output.weight", quantization="Q4_K", ggml_type=12,
              dimensions=[5120, 248320], offset=10996640, bytes=715161600)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def helpers():
    # Git may convert line endings in Windows checkouts.
    raw = SCALE_HELPER.read_bytes().replace(b"\r\n", b"\n")
    require(sha256(raw).hexdigest() == SCALE_HELPER_SHA256, "Historical scale helper SHA-256 differs")
    scope = {"__name__": "pinned_scale_replay", "__file__": str(SCALE_HELPER)}
    exec(compile(raw, str(SCALE_HELPER), "exec"), scope)
    return scope, scope["replay_helpers"]()


def code_position(coordinate, row_bytes):
    require(type(coordinate) is int and 0 <= coordinate < row_bytes // 144 * 256,
            "Expected an in-range Q4_K code coordinate")
    block, index = divmod(coordinate, 256)
    group, lane = divmod(index, 32)
    return block * 144 + 16 + 32 * (group // 2) + lane, 4 * (group % 2)


def code_changes(entries, row_bytes, maximum_step):
    require(isinstance(entries, list) and entries, "Expected declared Q4_K code changes")
    moves = []
    previous = -1
    for entry in entries:
        require(isinstance(entry, dict)
                and set(entry) == {"coordinate", "signed_code_delta", "before", "after"},
                "Expected one signed change with both code endpoints")
        coordinate, delta, before, after = (entry[key] for key in ("coordinate", "signed_code_delta", "before", "after"))
        offset, shift = code_position(coordinate, row_bytes)
        require(coordinate > previous and all(type(x) is int for x in (delta, before, after))
                and 1 <= abs(delta) <= maximum_step and 0 <= before <= 15 and 0 <= after <= 15 and after - before == delta,
                "Expected unique, ordered, legal signed Q4_K code endpoints")
        moves.append((offset, shift, before, after))
        previous = coordinate
    return tuple(moves)


def group_changes(entries, row_bytes):
    require(isinstance(entries, list), "Expected declared Q4_K group fields")
    moves = []
    previous = (-1, -1, "")
    for entry in entries:
        require(isinstance(entry, dict) and set(entry) == {"block", "group", "field", "before", "after"},
                "Expected a named Q4_K group field with both endpoints")
        block, group, field, before, after = (entry[key] for key in ("block", "group", "field", "before", "after"))
        require(type(block) is int and 0 <= block < row_bytes // 144
                and type(group) is int and 0 <= group < 8
                and isinstance(field, str) and field in GROUP_FIELD_INDEX
                and (block, group, field) > previous
                and all(type(value) is int and 0 <= value <= 63 for value in (before, after))
                and before != after, "Expected unique, ordered, legal Q4_K group endpoints")
        index = GROUP_FIELD_INDEX[field]
        start = block * 144 + 4
        # Groups 4-7 split high bits from the low nibble shared by scale and minimum.
        if group < 4:
            parts = ((start + group + 4 * index, 0x3f, 0, 0),)
        else:
            parts = ((start + group - 4 + 4 * index, 0xc0, 6, 4),
                     (start + group + 4, 0xf << (4 * index), 4 * index, 0))
        moves.append((parts, before, after))
        previous = block, group, field
    return tuple(moves)


def load_capsule(scale, replay, pilot):
    capsule_sha, field_count, code_count, maximum_step, group_count = CAPSULES[pilot]
    path = replay["EVIDENCE"] / f"direct-closure-pilot-{pilot}-row-patch.json"
    patch = json.loads(path.read_bytes())
    canonical = json.dumps(patch, sort_keys=True, separators=(",", ":")).encode("ascii")
    schema = ("public-direct-output-multirow-q4k-mixed-group-patch-v1" if group_count
              else "public-direct-output-multirow-q4k-mixed-patch-v1")
    require(sha256(canonical).hexdigest() == capsule_sha and patch["pilot"] == pilot and patch["schema"] == schema,
            f"Pilot {pilot} mixed capsule SHA-256 or schema differs")
    require(patch["tensor"] == TENSOR and patch["checkpoint_bytes"] == CHECKPOINT_BYTES
            and patch["parent_sha256"] == PARENT_SHA256, "Expected the exact Pilot 024 Q4_K output tensor")
    rows = patch["rows"]
    require(tuple(row["token_id"] for row in rows) == TOKENS, "Expected the four pinned rows in physical order")
    changes = []
    for row in rows:
        require(row["bytes"] == ROW_BYTES and row["offset"] == TENSOR["offset"] + row["token_id"] * ROW_BYTES,
                "Patch tensor and row extents disagree")
        groups = group_changes(row["changed_group_fields"], ROW_BYTES) if group_count else ()
        changes.append((scale["row_fields"](row["changed_fields"], ROW_BYTES),
                        code_changes(row["changed_codes"], ROW_BYTES, maximum_step), groups))
    require(sum(len(fields) for fields, _, _ in changes) == patch["changed_binary16_fields"] == field_count
            and sum(len(codes) for _, codes, _ in changes) == patch["changed_code_nibbles"] == code_count
            and sum(len(groups) for _, _, groups in changes) == patch.get("changed_group_fields", 0) == group_count,
            "Total binary16, nibble or group field count differs")
    return patch, tuple(changes)


def row_masks(original, row, fields, codes, groups=()):
    require(len(original) == row["bytes"] and sha256(original).hexdigest() == row["parent_sha256"],
            "Parent row SHA-256 differs")
    edited = bytearray(original)
    allowed = {}
    for offset, before, after in fields:
        require(original[offset:offset + 2] == before, "Declared parent binary16 bytes differ")
        edited[offset:offset + 2] = after
        allowed[offset] = allowed[offset + 1] = 255
    for offset, shift, before, after in codes:
        require((original[offset] >> shift) & 15 == before, "Declared parent Q4_K code differs")
        nibble = 15 << shift
        require(not allowed.get(offset, 0) & nibble, "Declared packed edits overlap")
        edited[offset] = (edited[offset] & ~nibble) | (after << shift)
        allowed[offset] = allowed.get(offset, 0) | nibble
    for parts, before, after in groups:
        current = sum(((original[offset] & mask) >> shift) << value_shift
                      for offset, mask, shift, value_shift in parts)
        require(current == before, "Declared parent Q4_K group field differs")
        for offset, mask, shift, value_shift in parts:
            require(not allowed.get(offset, 0) & mask, "Declared packed edits overlap")
            edited[offset] = (edited[offset] & ~mask) | (((after >> value_shift) << shift) & mask)
            allowed[offset] = allowed.get(offset, 0) | mask
    changes = tuple((offset, left ^ right) for offset, (left, right) in
                    enumerate(zip(original, edited, strict=True)) if left != right)
    require(all(not mask & ~allowed.get(offset, 0) for offset, mask in changes),
            "Undeclared partner nibble or group metadata bit changed")
    require(sha256(edited).hexdigest() == row["candidate_sha256"], "Replayed row SHA-256 differs")
    return changes


def checked_masks(parent, patch, changes, replay):
    masks = []
    with parent.open("rb") as source:
        info = os.fstat(source.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size == patch["checkpoint_bytes"],
                "Parent must be a regular file of the pinned size")
        for row, row_changes in replay["row_patches"](patch, changes):
            source.seek(row["offset"])
            original = replay["read_exact"](source, row["bytes"])
            masks.append(row_masks(original, row, *row_changes))
    require(sum(map(len, masks)) == patch["changed_bytes"], "Physical changed-byte count differs")
    if "changed_group_fields" in patch:
        group_xors = [xor for row in masks for offset, xor in row if 4 <= offset % 144 < 16]
        require(len(group_xors) == patch["changed_group_metadata_bytes"]
                and sum(xor.bit_count() for xor in group_xors) == patch["changed_group_metadata_bits"]
                and sum(xor.bit_count() for row in masks for _, xor in row) == patch["changed_bits"],
                "Physical group metadata or total bit counts differ")
    return tuple(masks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=int, choices=CAPSULES, default=194, help="Published edit to replay")
    parser.add_argument("--parent", type=Path, required=True, help="Exact Pilot 024 parent GGUF")
    parser.add_argument("--output", type=Path, help="Optional fresh GGUF path on a hard-link-capable filesystem")
    args = parser.parse_args()
    try:
        scale, replay = helpers()
        patch, changes = load_capsule(scale, replay, args.pilot)
        masks = checked_masks(args.parent, patch, changes, replay)
        replay["replay"](args.parent, args.output, patch, masks)
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"Replay failed. {error}\n")
    print(json.dumps(dict(status="WRITTEN_AND_VERIFIED" if args.output else "VERIFIED_ONLY",
                          parent_sha256=patch["parent_sha256"], candidate_sha256=patch["candidate_sha256"],
                          changed_binary16_fields=patch["changed_binary16_fields"],
                          changed_code_nibbles=patch["changed_code_nibbles"], changed_bytes=patch["changed_bytes"],
                          **{key: patch[key] for key in GROUP_COUNTS if key in patch},
                          rows=[dict(token_id=row["token_id"], parent_row_sha256=row["parent_sha256"],
                                     candidate_row_sha256=row["candidate_sha256"], changed_bytes=len(xor))
                                for row, xor in replay["row_patches"](patch, masks)]), indent=2))


if __name__ == "__main__":
    main()
