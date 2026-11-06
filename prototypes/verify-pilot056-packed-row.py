"""Reproduce the published Pilot 056 Q4_K edit from its exact source GGUF."""

import argparse
import hashlib
import json
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "direct-accuracy-pilots-055-056-up-projection.json"


def verify(model, evidence):
    tensor = evidence["tensor"]
    recipe = evidence["probe_recipe"]
    block, local = divmod(recipe["input_coordinate"], 256)
    group, lane = divmod(local, 32)
    index = block * 144 + 16 + (group // 2) * 32 + lane
    shift = 4 * (group % 2)
    row_offset = tensor["offset"] + recipe["neuron"] * tensor["row_bytes"]
    if (index, shift, row_offset + index) != (
        recipe["row_relative_byte_offset"], recipe["nibble_shift"], recipe["absolute_model_byte_offset"]
    ):
        raise ValueError("Calculated Q4_K location differs from the published recipe")

    with model.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != evidence["parent_checkpoint_sha256"]:
            raise ValueError("Source GGUF differs from the published parent checkpoint")
        source.seek(row_offset)
        parent = source.read(tensor["row_bytes"])
    if hashlib.sha256(parent).hexdigest() != recipe["parent_row_sha256"]:
        raise ValueError("Source Q4_K row SHA-256 differs")

    old_code = (parent[index] >> shift) & 15
    new_code = old_code + recipe["code_delta"]
    if not 0 <= new_code <= 15:
        raise ValueError("Edited Q4_K code would overflow its nibble")
    edited = bytearray(parent)
    edited[index] ^= (old_code ^ new_code) << shift
    edited_sha256 = hashlib.sha256(edited).hexdigest()
    if edited_sha256 != recipe["edited_row_sha256"]:
        raise ValueError("Reconstructed Q4_K row SHA-256 differs")
    return {
        "tensor": tensor["name"],
        "neuron": recipe["neuron"],
        "input_coordinate": recipe["input_coordinate"],
        "absolute_byte_offset": row_offset + index,
        "old_code": old_code,
        "new_code": new_code,
        "changed_bytes": sum(before != after for before, after in zip(parent, edited, strict=True)),
        "edited_row_sha256": edited_sha256,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("model", type=Path, help="Path to the exact Pilot 024 parent GGUF")
    result = verify(cli.parse_args().model, json.loads(EVIDENCE.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))
