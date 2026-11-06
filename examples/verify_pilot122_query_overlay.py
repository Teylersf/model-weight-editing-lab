"""Verify the eight published Pilot 122 IQ4_XS query recipes without GPU or model writes."""

import argparse
import hashlib
import json
from pathlib import Path
import re


RECEIPT = Path(__file__).resolve().parents[1] / "evidence/direct-accuracy-pilot-122-query-overlay.json"
TENSOR = "blk.63.attn_q.weight"
TENSOR_OFFSET = 10_832_088_992
ROW_BYTES = 2720
WIDTH = 5120
ROW_COUNT = 12_288
HEX = re.compile(r"[a-f0-9]{64}")
CODE = re.compile(r"(0|[1-9][0-9]*):([+-]1)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_patch(recipe):
    lines = recipe["patch_lines"]
    encoded = ("\n".join(lines) + "\n").encode("ascii")
    require(hashlib.sha256(encoded).hexdigest() == recipe["patch_sha256"], "TSV digest differs")
    require(lines[0] == "IQ4_XS_QUERY_PATCH_V1" and 2 <= len(lines) <= 17, "Invalid TSV header or row count")
    rows = {}
    for line in lines[1:]:
        index, parent, edited, codes = line.split("\t")
        row = int(index)
        require(index == str(row) and 0 <= row < ROW_COUNT and row % 512 < 256 and
                (not rows or row > next(reversed(rows))), "Query rows must be sorted and outside the gate half")
        require(HEX.fullmatch(parent) and HEX.fullmatch(edited) and parent != edited, "Invalid row digests")
        entries = []
        for change in codes.split(" "):
            match = CODE.fullmatch(change)
            require(match, "Invalid code edit")
            column, delta = map(int, match.groups())
            require(column < WIDTH and (not entries or column > entries[-1][0]), "Duplicate, unsorted or invalid column")
            entries.append((column, delta))
        rows[row] = parent, edited, entries
    count = sum(len(entries) for _, _, entries in rows.values())
    require(len(rows) == recipe["changed_rows"] and 1 <= count == recipe["changed_codes"] <= 32, "Edit counts differ")
    return rows


def edited_row(packed, entries):
    result = bytearray(packed)
    for column, delta in entries:
        block, within = divmod(column, 256)
        group, lane = divmod(within, 32)
        index = 136 * block + 8 + 16 * group + lane % 16
        shift = 4 * (lane // 16)
        code = ((result[index] >> shift) & 15) + delta
        require(0 <= code <= 15, "IQ4_XS code crosses a legal endpoint")
        result[index] = (result[index] & ~(15 << shift)) | (code << shift)
    return result


def verify(receipt, model=None):
    require(receipt["schema"] == "pilot122-native-query-overlay-public-v1" and
            receipt["tensor"] == {"name": TENSOR, "dimensions": [WIDTH, ROW_COUNT], "ggml_type": 23,
                                  "offset": TENSOR_OFFSET, "row_bytes": ROW_BYTES}, "Unexpected tensor or receipt")
    recipes = receipt["candidates"]
    require([item["candidate"] for item in recipes] == list(range(1, 9)) and
            len({item["patch_sha256"] for item in recipes}) == 8, "Expected eight distinct candidates")
    rows = [parse_patch(recipe) for recipe in recipes]
    checked = 0
    if model is not None:
        with model.open("rb") as stream:
            parent = receipt["parent"]
            require(model.stat().st_size == parent["bytes"] and
                    hashlib.file_digest(stream, "sha256").hexdigest() == parent["sha256"], "Full parent identity differs")
            for recipe in rows:
                for index, (before, after, entries) in recipe.items():
                    stream.seek(TENSOR_OFFSET + ROW_BYTES * index)
                    packed = stream.read(ROW_BYTES)
                    require(len(packed) == ROW_BYTES and hashlib.sha256(packed).hexdigest() == before,
                            "Packed parent row digest differs")
                    require(hashlib.sha256(edited_row(packed, entries)).hexdigest() == after,
                            "Rebuilt edited row digest differs")
                    checked += 1
    return {"recipes_verified": len(rows), "code_edits_across_recipes": sum(item["changed_codes"] for item in recipes),
            "exact_parent_and_edited_rows_verified": checked, "full_parent_verified": model is not None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, help="Optional exact Pilot 024 GGUF for packed-row readback")
    args = parser.parse_args()
    print(json.dumps(verify(json.loads(RECEIPT.read_text(encoding="utf-8")), args.model)))


if __name__ == "__main__":
    main()
