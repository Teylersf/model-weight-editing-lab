"""Verify or replay a published Pilot output-row patch on its pinned GGUF parent."""

import argparse
from contextlib import nullcontext
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import tempfile


EVIDENCE = Path(__file__).resolve().parent.parent / "evidence"
CAPSULE_CONTENT_SHA256 = {
    16: "ae86395f27b64fc20797003ab468c9df6cba8ebac9e29b378328fd2d74b140cd",
    17: "7c5f1942b2ca9aabbc110e80fae148e72f8cc570689c7265551c25abc664bfe0",
    18: "e26186ca7a31672ceb62f55ad2de96dd1aa8efc1d1faaf073642d789233f250f",
    19: "8eb077cb71119294acca75a14f5500c112382361a7c77e0d4a0a5229a56f1c7d",
    20: "abd5019a5478eb88c23db87f2307a76a58154349bc22c6d13590ad0e87b105e4",
    21: "80b3ddc115098acdfeb4ac8c4d14714d233cb1ef7dbbdf081021f42fbae46fa6",
    24: "ffd8d6c1328ddfe57e120c169376e3c8004bd769481ada1b12ee148536df0c96",
    27: "d318e769db6aea75215fb76b5e0d39ec86f100b963326380313ad9ad719f01a3",
}
CHUNK_BYTES = 8 * 1024 * 1024
GGUF_SCALAR_BYTES = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_capsule(pilot=16):
    capsule = EVIDENCE / f"direct-closure-pilot-{pilot:03d}-row-patch.json"
    patch = json.loads(capsule.read_bytes())
    # Canonical JSON keeps the pin independent of checkout line endings.
    canonical = json.dumps(patch, sort_keys=True, separators=(",", ":")).encode("ascii")
    require(digest(canonical) == CAPSULE_CONTENT_SHA256[pilot] and patch["pilot"] == pilot,
            f"Pilot {pilot:03d} patch capsule SHA-256 differs")

    tensor = patch["tensor"]
    width, count = tensor["dimensions"]
    require(tensor["ggml_type"] == 12 and tensor["quantization"] == "Q4_K" and width % 256 == 0,
            "Patch does not describe a packed Q4_K row")
    row_bytes = width // 256 * 144
    require(tensor["bytes"] == count * row_bytes
            and 0 <= tensor["offset"] < tensor["offset"] + tensor["bytes"] <= patch["checkpoint_bytes"],
            "Patch tensor extent differs")

    multirow = patch["schema"] == "public-direct-output-multirow-xor-patch-v1"
    if multirow:
        rows = patch["rows"]
        tokens = [row["token_id"] for row in rows]
        require(len(rows) > 1 and tokens == sorted(set(tokens)), "Patch rows must be unique and ordered")
    else:
        require(patch["schema"] == "public-direct-output-row-xor-patch-v1", "Unsupported patch schema")
        rows = [dict(patch["row"], sparse_xor=patch["sparse_xor"])]
    changes = []
    for row in rows:
        require(0 <= row["token_id"] < count and row["bytes"] == row_bytes
                and row["offset"] == tensor["offset"] + row["token_id"] * row_bytes,
                "Patch tensor and row extents disagree")
        changes.append(read_sparse_xor(row["sparse_xor"], row_bytes))
    if multirow:
        require(sum(map(len, changes)) == patch["changed_bytes"], "Total changed-byte count differs")
    return patch, tuple(changes) if multirow else changes[0]


def read_sparse_xor(sparse, row_bytes):
    offsets, values = sparse["row_relative_offsets"], bytes.fromhex(sparse["xor_hex"])
    require(0 < len(offsets) == len(values) == sparse["changed_bytes"]
            and offsets == sorted(set(offsets)) and 0 <= offsets[0] <= offsets[-1] < row_bytes and all(values),
            "Patch sparse XOR data is malformed")
    require(all(offset % 144 >= 16 for offset in offsets), "Patch touches Q4_K block metadata")
    return tuple(zip(offsets, values, strict=True))


def row_patches(patch, xor):
    if "rows" in patch:
        return list(zip(patch["rows"], xor, strict=True))
    return [(patch["row"], xor)]


def read_exact(stream, size):
    data = stream.read(size)
    require(len(data) == size, "Unexpected end of file")
    return data


def unpack(stream, layout):
    return struct.unpack(layout, read_exact(stream, struct.calcsize(layout)))


def read_gguf_string(stream, header_bytes):
    size, = unpack(stream, "<Q")
    require(size <= header_bytes - stream.tell(), "GGUF string exceeds the header")
    return read_exact(stream, size)


def skip_gguf_value(stream, kind, header_bytes):
    element_count = 1
    if kind == 9:
        kind, element_count = unpack(stream, "<IQ")
    if kind == 8:
        require(element_count <= header_bytes // 8, "GGUF string array exceeds the header")
        for _ in range(element_count):
            size, = unpack(stream, "<Q")
            require(size <= header_bytes - stream.tell(), "GGUF string exceeds the header")
            stream.seek(size, os.SEEK_CUR)
    else:
        require(kind in GGUF_SCALAR_BYTES, "Unsupported GGUF metadata value type")
        size = element_count * GGUF_SCALAR_BYTES[kind]
        require(size <= header_bytes - stream.tell(), "GGUF metadata value exceeds the header")
        stream.seek(size, os.SEEK_CUR)


def verify_gguf_tensor(stream, tensor):
    # The pinned tensor offset bounds every metadata and tensor descriptor read.
    header_bytes = tensor["offset"]
    header = io.BytesIO(read_exact(stream, header_bytes))
    magic, version, tensors, metadata = unpack(header, "<4sIQQ")
    require((magic, version) == (b"GGUF", 3) and 0 < tensors <= 4096 and metadata <= 4096,
            "Parent must be the expected little-endian GGUF v3 file")
    alignment = 32
    for _ in range(metadata):
        key = read_gguf_string(header, header_bytes)
        kind, = unpack(header, "<I")
        if key == b"general.alignment":
            require(kind == 4, "GGUF alignment must be a uint32")
            alignment, = unpack(header, "<I")
        else:
            skip_gguf_value(header, kind, header_bytes)
    require(alignment > 0 and alignment & (alignment - 1) == 0, "Invalid GGUF alignment")

    descriptor = None
    for _ in range(tensors):
        name = read_gguf_string(header, header_bytes)
        dimensions, = unpack(header, "<I")
        require(1 <= dimensions <= 4, "Invalid GGUF tensor dimension count")
        shape = unpack(header, f"<{dimensions}Q")
        kind, relative_offset = unpack(header, "<IQ")
        if name == tensor["name"].encode("ascii"):
            require(descriptor is None, "GGUF tensor name appears more than once")
            descriptor = shape, kind, relative_offset

    require(descriptor is not None, "GGUF output tensor is missing")
    shape, kind, relative_offset = descriptor
    data_start = (header.tell() + alignment - 1) // alignment * alignment
    require(list(shape) == tensor["dimensions"] and kind == tensor["ggml_type"]
            and data_start + relative_offset == tensor["offset"], "GGUF output tensor metadata differs")
    stream.seek(0)


def copy_span(source, destination, parent_hash, candidate_hash, size):
    while size:
        data = read_exact(source, min(size, CHUNK_BYTES))
        parent_hash.update(data)
        candidate_hash.update(data)
        if destination is not None:
            destination.write(data)
        size -= len(data)


def apply_row_patch(source, destination, patch, xor):
    parent_hash = hashlib.sha256()
    candidate_hash = hashlib.sha256()
    cursor = 0
    for row, changes in row_patches(patch, xor):
        copy_span(source, destination, parent_hash, candidate_hash, row["offset"] - cursor)
        original = read_exact(source, row["bytes"])
        require(digest(original) == row["parent_sha256"], "Parent row SHA-256 differs")
        patched = bytearray(original)
        for offset, mask in changes:
            patched[offset] ^= mask
        require(digest(patched) == row["candidate_sha256"], "Replayed row SHA-256 differs")
        parent_hash.update(original)
        candidate_hash.update(patched)
        if destination is not None:
            destination.write(patched)
        cursor = row["offset"] + row["bytes"]

    copy_span(source, destination, parent_hash, candidate_hash, patch["checkpoint_bytes"] - cursor)
    require(source.read(1) == b"", "Parent contains trailing bytes")
    require(parent_hash.hexdigest() == patch["parent_sha256"], "Full parent SHA-256 differs")
    require(candidate_hash.hexdigest() == patch["candidate_sha256"], "Full replayed candidate SHA-256 differs")


def verify_staged(path, patch):
    state = hashlib.sha256()
    with path.open("rb") as staged:
        require(os.fstat(staged.fileno()).st_size == patch["checkpoint_bytes"], "Staged size differs")
        while data := staged.read(CHUNK_BYTES):
            state.update(data)
    require(state.hexdigest() == patch["candidate_sha256"], "Staged file readback SHA-256 differs")


def replay(parent, output, patch, xor):
    if output is not None:
        require(not os.path.lexists(output), "Output already exists. Choose a fresh path.")
    staged_path = None
    try:
        with parent.open("rb") as source:
            before = os.fstat(source.fileno())
            require(stat.S_ISREG(before.st_mode) and before.st_size == patch["checkpoint_bytes"],
                    "Parent must be a regular file of the pinned size")
            verify_gguf_tensor(source, patch["tensor"])
            target = nullcontext() if output is None else tempfile.NamedTemporaryFile(
                mode="wb", dir=output.parent, prefix=f".pilot-{patch['pilot']:03d}-", suffix=".part", delete=False)
            with target as staged:
                if staged is not None:
                    staged_path = Path(staged.name)
                apply_row_patch(source, staged, patch, xor)
                after = os.fstat(source.fileno())
                require((before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                        == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "Parent changed during replay")
                if staged is not None:
                    staged.flush()
                    os.fsync(staged.fileno())
        if staged_path is not None:
            verify_staged(staged_path, patch)
            # Publish verified bytes atomically, even if the destination appeared during replay.
            os.link(staged_path, output)
    finally:
        if staged_path is not None:
            staged_path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=int, choices=tuple(CAPSULE_CONTENT_SHA256), default=16,
                        help="Choose the patch capsule (default 16)")
    parser.add_argument("--parent", type=Path, required=True, help="Exact accepted parent GGUF")
    parser.add_argument("--output", type=Path, help="Optional fresh GGUF path on a hard-link-capable filesystem")
    args = parser.parse_args()
    try:
        patch, xor = load_capsule(args.pilot)
        replay(args.parent, args.output, patch, xor)
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"Replay failed. {error}\n")
    result = dict(status="WRITTEN_AND_VERIFIED" if args.output else "VERIFIED_ONLY",
                  parent_sha256=patch["parent_sha256"], candidate_sha256=patch["candidate_sha256"])
    if "rows" in patch:
        result["rows"] = [dict(token_id=row["token_id"], parent_row_sha256=row["parent_sha256"],
                               candidate_row_sha256=row["candidate_sha256"], changed_bytes=len(changes))
                          for row, changes in row_patches(patch, xor)]
        result["changed_bytes"] = patch["changed_bytes"]
    else:
        result.update(parent_row_sha256=patch["row"]["parent_sha256"],
                      candidate_row_sha256=patch["row"]["candidate_sha256"], changed_bytes=len(xor))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
