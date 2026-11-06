"""Replay the four-row binary32 correction on one archived native logit vector."""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import struct


WIDTH = 5120
VOCABULARY = 248320
TOKEN_IDS = (357, 417, 351, 414)


def unpack_f32(data, count):
    if len(data) != count * 4:
        raise ValueError(f"Expected {count} little-endian binary32 values")
    values = struct.unpack(f"<{count}f", data)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Input contains a nonfinite binary32 value")
    return values


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def effective_q8(hidden):
    result = []
    for start in range(0, WIDTH, 32):
        block = hidden[start:start + 32]
        maximum = max(map(abs, block))
        if maximum == 0:
            result.extend([0.0] * 32)
            continue
        scale = f32(maximum / 127)
        if scale == 0:
            raise ValueError("Q8 scale underflow")
        half_scale = struct.unpack("<e", struct.pack("<e", scale))[0]
        for value in block:
            quotient = f32(value / scale)
            code = math.copysign(math.floor(abs(quotient) + 0.5), quotient)
            if abs(code) > 127:
                raise ValueError("Q8 code is outside its signed range")
            result.append(code * half_scale if code else 0.0)
    return result


def replay(stock_logits, normalized_input, stock_rows, replacement_rows):
    logits = unpack_f32(stock_logits, VOCABULARY)
    hidden = unpack_f32(normalized_input, WIDTH)
    stock = unpack_f32(stock_rows, len(TOKEN_IDS) * WIDTH)
    replacement = unpack_f32(replacement_rows, len(TOKEN_IDS) * WIDTH)
    operand = effective_q8(hidden)
    result = bytearray(stock_logits)
    for lane, token in enumerate(TOKEN_IDS):
        start = lane * WIDTH
        correction = 0.0
        for coordinate, value in enumerate(operand, start):
            correction += value * (replacement[coordinate] - stock[coordinate])
        if correction:
            struct.pack_into("<f", result, token * 4, logits[token] + correction)
    return bytes(result)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--stock-logits", required=True, type=Path)
    cli.add_argument("--normalized-input", required=True, type=Path)
    cli.add_argument("--stock-rows", required=True, type=Path)
    cli.add_argument("--replacement-rows", required=True, type=Path)
    cli.add_argument("--output", type=Path)
    args = cli.parse_args()
    stock_logits = args.stock_logits.read_bytes()
    corrected = replay(stock_logits, args.normalized_input.read_bytes(),
                       args.stock_rows.read_bytes(), args.replacement_rows.read_bytes())
    if args.output is not None:
        with args.output.open("xb") as stream:
            stream.write(corrected)
    changed = [token for token in TOKEN_IDS
               if corrected[token * 4:token * 4 + 4] != stock_logits[token * 4:token * 4 + 4]]
    print(json.dumps({"stock_sha256": sha256(stock_logits).hexdigest(),
                      "corrected_sha256": sha256(corrected).hexdigest(),
                      "changed_token_ids": changed, "wrote_output": args.output is not None}))


if __name__ == "__main__":
    main()
