"""Verify the exact Pilot 026 or 033 low-rank D63 replay without writing a GGUF."""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import runpy
import stat
import struct
import zlib

import numpy as np


HERE = Path(__file__).resolve().parent
CAPSULES = {
    26: ("two", 2, "d5259bf4f303aaddbdbc4747e41f5695e87b10e9f736a3d244f1ae754ab83feb"),
    33: ("three", 3, "70b2ede4d4ee589c021e8fd1d5abbe14c38635bbd49bcd1fc9664296ca1a9a56"),
}
ROW_BLOCK = 64
HELPERS = runpy.run_path(str(HERE / "replay_d63_rank_one_edit.py"))
require = HELPERS["require"]


def load_capsule(pilot=26):
    rank_name, rank, capsule_sha = CAPSULES[pilot]
    capsule = HERE.parent / f"evidence/direct-accuracy-pilot-{pilot:03}-d63-patch.json"
    patch = json.loads(capsule.read_bytes())
    canonical = json.dumps(patch, sort_keys=True, separators=(",", ":")).encode("ascii")
    require(sha256(canonical).hexdigest() == capsule_sha, f"Pilot {pilot:03} patch capsule SHA-256 differs")
    tensor = patch["tensor"]
    columns, rows = tensor["dimensions"]
    require(patch["schema"] == f"public-direct-d63-rank-{rank_name}-patch-v1" and patch["pilot"] == pilot
            and patch["factor_encoding"] == "base64+zlib" and patch["factor_dtype"] == "<f8"
            and tensor["name"] == "blk.63.ffn_down.weight" and tensor["ggml_type"] == 0 and tensor["type"] == "F32"
            and (columns, rows) == (17408, 5120) and tensor["bytes"] == columns * rows * 4
            and 0 < tensor["gguf_data_offset"] <= min(tensor["offset"], 16 * 1024 * 1024)
            and tensor["offset"] + tensor["bytes"] <= patch["checkpoint_bytes"], "Invalid F32 D63 patch extent")
    u, v = patch["factors"]["u"], patch["factors"]["v"]
    require(u["shape"] == [rows, rank] and v["shape"] == [columns, rank], "Low-rank factor shape differs")
    factor = HELPERS["factor"]
    return patch, factor(u, rows * rank).reshape(rows, rank), factor(v, columns * rank).reshape(columns, rank)


def rounded_blocks(source, u, v):
    with np.errstate(over="raise", invalid="raise"):
        for start in range(0, len(u), ROW_BLOCK):
            rows = u[start:start + ROW_BLOCK]
            raw = HELPERS["read_exact"](source, len(rows) * len(v) * 4)
            before = np.frombuffer(raw, dtype="<f4").reshape(len(rows), len(v)).astype(np.float64)
            require(np.isfinite(before).all(), "Parent tensor has a nonfinite value")
            correction = np.multiply(rows[:, 0, None], v[None, :, 0], dtype=np.float64)
            if u.shape[1] == 3:
                # Pilot 033's streamed fit starts the F64 sum from zero.
                np.add(0., correction, out=correction)
            for column in range(1, u.shape[1]):
                term = np.multiply(rows[:, column, None], v[None, :, column], dtype=np.float64)
                np.add(correction, term, out=correction)
            np.add(before, correction, out=before)
            after = before.astype("<f4")
            require(np.isfinite(after).all(), "Replayed tensor has a nonfinite value")
            yield raw, after.tobytes()


def verify(parent, patch, u, v, tensor_only):
    tensor = patch["tensor"]
    model_before, model_after, d63_before, d63_after = (sha256() for _ in range(4))
    hash_unchanged = HELPERS["hash_unchanged"]
    with parent.open("rb") as source:
        before = os.fstat(source.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size == patch["checkpoint_bytes"],
                "Parent must be a regular file of the pinned size")
        HELPERS["verify_d63_descriptor"](source, tensor)
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
            require(model_before.hexdigest() == patch["parent_sha256"], "Full Pilot 024 parent SHA-256 differs")
            require(model_after.hexdigest() == patch["candidate_sha256"], "Full replayed candidate SHA-256 differs")
        after = os.fstat(source.fileno())
        require((before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                == (after.st_size, after.st_mtime_ns, after.st_ctime_ns), "Parent changed during replay")

    result = dict(status="D63_VERIFIED_ONLY" if tensor_only else "VERIFIED_ONLY", pilot=patch["pilot"], tensor=tensor["name"],
                  tensor_bytes=tensor["bytes"], parent_D63_sha256=d63_before.hexdigest(),
                  candidate_D63_sha256=d63_after.hexdigest())
    if not tensor_only:
        result.update(checkpoint_bytes=patch["checkpoint_bytes"], parent_sha256=model_before.hexdigest(),
                      candidate_sha256=model_after.hexdigest())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=int, choices=CAPSULES, default=26)
    parser.add_argument("--parent", type=Path, required=True, help="Exact Pilot 024 GGUF")
    parser.add_argument("--tensor-only", action="store_true", help="Verify D63 hashes without reading the full GGUF")
    args = parser.parse_args()
    try:
        patch, u, v = load_capsule(args.pilot)
        result = verify(args.parent, patch, u, v, args.tensor_only)
    except (OSError, ValueError, FloatingPointError, struct.error, zlib.error) as error:
        parser.exit(1, f"Replay failed. {error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
