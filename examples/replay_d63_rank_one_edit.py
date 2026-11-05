"""Verify Pilot 023 by streaming a rank-one D63 replay without writing a GGUF."""

import argparse
import base64
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import stat
import struct
import zlib

import numpy as np


CAPSULE = Path(__file__).resolve().parent.parent / "evidence/direct-closure-pilot-023-d63-patch.json"
CAPSULE_SHA256 = "cdf8a59d126575529aad788abe904e0b08f1ba6a9ff0c322a48dc94605df8208"
ROW_BLOCK = 64
SPAN_BLOCK = 8 * 1024 * 1024
SCALAR_BYTES = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def factor(spec, count):
    size = count * 8
    require(spec["elements"] == count and spec["bytes"] == size, "Factor extent differs")
    packed = base64.b64decode(spec["data"], validate=True)
    stream = zlib.decompressobj()
    raw = stream.decompress(packed, size + 1)
    require(stream.eof and not stream.unused_data and not stream.unconsumed_tail and len(raw) == size
            and sha256(raw).hexdigest() == spec["sha256"], "Factor bytes or SHA-256 differ")
    values = np.frombuffer(raw, dtype="<f8")
    require(np.isfinite(values).all() and np.any(values), "Factor contains invalid F64 values")
    return values


def load_capsule():
    patch = json.loads(CAPSULE.read_bytes())
    canonical = json.dumps(patch, sort_keys=True, separators=(",", ":")).encode("ascii")
    require(sha256(canonical).hexdigest() == CAPSULE_SHA256, "Pilot 023 patch capsule SHA-256 differs")
    tensor = patch["tensor"]
    columns, rows = tensor["dimensions"]
    require(patch["schema"] == "public-direct-d63-rank-one-patch-v1" and patch["pilot"] == 23
            and patch["factor_encoding"] == "base64+zlib" and patch["factor_dtype"] == "<f8"
            and tensor["name"] == "blk.63.ffn_down.weight" and tensor["ggml_type"] == 0 and tensor["type"] == "F32"
            and columns > 0 and rows > 0 and tensor["bytes"] == columns * rows * 4
            and 0 < tensor["gguf_data_offset"] <= min(tensor["offset"], 16 * 1024 * 1024)
            and tensor["offset"] + tensor["bytes"] <= patch["checkpoint_bytes"], "Invalid F32 D63 patch extent")
    return patch, factor(patch["factors"]["u"], rows), factor(patch["factors"]["v"], columns)


def read_exact(stream, size):
    data = stream.read(size)
    require(len(data) == size, "Unexpected end of GGUF")
    return data


def unpack(stream, layout):
    return struct.unpack(layout, read_exact(stream, struct.calcsize(layout)))


def gguf_string(stream, bound, keep):
    size, = unpack(stream, "<Q")
    require(size <= bound - stream.tell(), "GGUF string exceeds the bounded header")
    if keep:
        return read_exact(stream, size)
    stream.seek(size, os.SEEK_CUR)


def skip_value(stream, kind, bound):
    count = 1
    if kind == 9:
        kind, count = unpack(stream, "<IQ")
    if kind == 8:
        require(count <= bound // 8, "GGUF string array exceeds the bounded header")
        for _ in range(count):
            gguf_string(stream, bound, keep=False)
    else:
        require(kind in SCALAR_BYTES, "Unsupported GGUF metadata value type")
        size = count * SCALAR_BYTES[kind]
        require(size <= bound - stream.tell(), "GGUF metadata exceeds the bounded header")
        stream.seek(size, os.SEEK_CUR)


def verify_d63_descriptor(source, tensor):
    # D63 starts far into the file. Read the header only, never the whole prefix.
    bound = tensor["gguf_data_offset"]
    header = io.BytesIO(read_exact(source, bound))
    magic, version, tensors, metadata = unpack(header, "<4sIQQ")
    require((magic, version) == (b"GGUF", 3) and 0 < tensors <= 4096 and metadata <= 4096,
            "Expected a little-endian GGUF v3 checkpoint")
    alignment = 32
    for _ in range(metadata):
        key = gguf_string(header, bound, keep=True)
        kind, = unpack(header, "<I")
        if key == b"general.alignment":
            require(kind == 4, "GGUF alignment must be a uint32")
            alignment, = unpack(header, "<I")
        else:
            skip_value(header, kind, bound)
    require(alignment > 0 and alignment & (alignment - 1) == 0, "Invalid GGUF alignment")
    match = None
    for _ in range(tensors):
        name = gguf_string(header, bound, keep=True)
        dimensions, = unpack(header, "<I")
        require(1 <= dimensions <= 4, "Invalid GGUF tensor dimensions")
        shape = unpack(header, f"<{dimensions}Q")
        kind, relative_offset = unpack(header, "<IQ")
        if name == tensor["name"].encode("ascii"):
            require(match is None, "Duplicate D63 tensor descriptor")
            match = (list(shape), kind, relative_offset)
    data_offset = (header.tell() + alignment - 1) // alignment * alignment
    require(data_offset == bound and match == (tensor["dimensions"], tensor["ggml_type"], tensor["offset"] - data_offset),
            "D63 tensor descriptor differs from the capsule")
    source.seek(0)


def hash_unchanged(source, size, original, candidate):
    while size:
        data = read_exact(source, min(size, SPAN_BLOCK))
        original.update(data)
        candidate.update(data)
        size -= len(data)


def rounded_blocks(source, u, v):
    with np.errstate(over="raise", invalid="raise"):
        for start in range(0, len(u), ROW_BLOCK):
            rows = u[start:start + ROW_BLOCK]
            raw = read_exact(source, len(rows) * len(v) * 4)
            before = np.frombuffer(raw, dtype="<f4").reshape(len(rows), len(v)).astype(np.float64)
            require(np.isfinite(before).all(), "Parent tensor has a nonfinite value")
            # Separate ufuncs materialize the F64 product before the F64 addition.
            update = np.multiply(rows[:, None], v[None, :], dtype=np.float64)
            np.add(before, update, out=before)
            after = before.astype("<f4")
            require(np.isfinite(after).all(), "Replayed tensor has a nonfinite value")
            yield raw, after.tobytes()


def verify(parent, patch, u, v, tensor_only):
    tensor = patch["tensor"]
    model_before, model_after, d63_before, d63_after = (sha256() for _ in range(4))
    with parent.open("rb") as source:
        before = os.fstat(source.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size == patch["checkpoint_bytes"],
                "Parent must be a regular file of the pinned size")
        verify_d63_descriptor(source, tensor)
        if tensor_only:
            source.seek(tensor["offset"])
        else:
            hash_unchanged(source, tensor["offset"], model_before, model_after)
        for old, new in rounded_blocks(source, u, v):
            d63_before.update(old)
            d63_after.update(new)
            if not tensor_only:
                model_before.update(old)
                model_after.update(new)
        require(source.tell() == tensor["offset"] + tensor["bytes"], "D63 replay extent differs")
        require(d63_before.hexdigest() == tensor["parent_sha256"], "Parent D63 SHA-256 differs")
        require(d63_after.hexdigest() == tensor["candidate_sha256"], "Replayed D63 SHA-256 differs")
        if not tensor_only:
            hash_unchanged(source, patch["checkpoint_bytes"] - source.tell(), model_before, model_after)
            require(source.read(1) == b"", "Parent contains trailing bytes")
            require(model_before.hexdigest() == patch["parent_sha256"], "Full parent SHA-256 differs")
            require(model_after.hexdigest() == patch["candidate_sha256"], "Full replayed candidate SHA-256 differs")
        after = os.fstat(source.fileno())
        require((before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "Parent changed during replay")
    result = dict(status="D63_VERIFIED_ONLY" if tensor_only else "VERIFIED_ONLY", tensor=tensor["name"],
                  tensor_bytes=tensor["bytes"], parent_D63_sha256=d63_before.hexdigest(),
                  candidate_D63_sha256=d63_after.hexdigest())
    if not tensor_only:
        result.update(checkpoint_bytes=patch["checkpoint_bytes"], parent_sha256=model_before.hexdigest(),
                      candidate_sha256=model_after.hexdigest())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True, help="Exact accepted parent GGUF")
    parser.add_argument("--tensor-only", action="store_true", help="Verify D63 hashes without reading the full GGUF")
    args = parser.parse_args()
    try:
        patch, u, v = load_capsule()
        result = verify(args.parent, patch, u, v, args.tensor_only)
    except (OSError, ValueError, FloatingPointError, struct.error, zlib.error) as error:
        parser.exit(1, f"Replay failed. {error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
