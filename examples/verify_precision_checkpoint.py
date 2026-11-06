"""Verify the full saved Pilot 275 precision-aware checkpoint on CPU."""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import struct


BASE_BYTES = 11674147744
BASE_SHA256 = "674c1e84a2adbf0232b6bb3d4d24a4d00f7c60b109d665f3fe5c88a484589db3"
ROWS_SHA256 = "701cc8fa89afd79cbed3294357b6b56d658a2d1d690512561c7707782e6e0af5"
CANDIDATE_SHA256 = "31d55cf331bb41ad4fb089beda24b5511a0781b4899380283161a52a371fb0b0"
ROWS, COLUMNS = 4, 5120
TOKENS = (357, 417, 351, 414)
PAYLOAD_BYTES = ROWS * COLUMNS * 4
FOOTER = struct.Struct("<8sQQII4I32s32s")
CHUNK_BYTES = 16 * 1024 * 1024


def verify(path):
    digest = sha256()
    remaining = BASE_BYTES
    with path.open("rb") as stream:
        while remaining:
            block = stream.read(min(remaining, CHUNK_BYTES))
            if not block:
                raise ValueError("Truncated Pilot 024 prefix")
            digest.update(block)
            remaining -= len(block)
        if digest.hexdigest() != BASE_SHA256:
            raise ValueError("Pilot 024 prefix hash differs")
        payload = stream.read(PAYLOAD_BYTES)
        footer = stream.read(FOOTER.size)
        if len(payload) != PAYLOAD_BYTES or len(footer) != FOOTER.size or stream.read(1):
            raise ValueError("Unexpected precision payload or footer extent")
    expected_footer = FOOTER.pack(b"WRF32R01", BASE_BYTES, PAYLOAD_BYTES, ROWS, COLUMNS,
                                  *TOKENS, bytes.fromhex(BASE_SHA256), bytes.fromhex(ROWS_SHA256))
    if footer != expected_footer or sha256(payload).hexdigest() != ROWS_SHA256:
        raise ValueError("Frozen precision footer or weight row bytes differ")
    if not all(math.isfinite(value) for (value,) in struct.iter_unpack("<f", payload)):
        raise ValueError("A replacement row contains nonfinite weights")
    digest.update(payload)
    digest.update(footer)
    if digest.hexdigest() != CANDIDATE_SHA256:
        raise ValueError("Whole precision checkpoint hash differs")
    return payload


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--checkpoint", required=True, type=Path)
    cli.add_argument("--extract-rows", type=Path)
    args = cli.parse_args()
    payload = verify(args.checkpoint)
    if args.extract_rows is not None:
        with args.extract_rows.open("xb") as out:
            out.write(payload)
    print(json.dumps({"status": "VERIFIED", "checkpoint_sha256": CANDIDATE_SHA256,
                      "prefix_sha256": BASE_SHA256, "replacement_rows_sha256": ROWS_SHA256,
                      "replacement_token_ids": TOKENS, "replacement_rows_extracted": args.extract_rows is not None}))


if __name__ == "__main__":
    main()
