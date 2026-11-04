"""Check a rerun against the reviewed ordinary CUDA proof pair."""

import argparse
import hashlib
import json
from pathlib import Path
import struct


def digest(data):
    return hashlib.sha256(data).hexdigest()


def id_digest(ids):
    return digest(b"".join(struct.pack("<i", token) for token in ids))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checkpoint_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(manifest, result, log):
    require(manifest["schema"] == "public-rank-two-exact-ordinary-proof-pair-v1"
            and len(manifest["cases"]) == 2, "Unexpected proof pair manifest")
    require(result["schema_version"] == 1, "Unexpected result schema")
    for key, value in manifest["backend"].items():
        require(result["backend"][key] == value, f"Backend differs: {key}")
    for key, value in manifest["parameters"].items():
        require(result["params"][key] == value, f"Parameter differs: {key}")
    require(b"offloaded 66/66 layers to GPU" in log, "Full CUDA offload missing")

    events = [json.loads(line.removeprefix(b"WR_LIVE ")) for line in log.splitlines()
              if line.startswith(b"WR_LIVE ")]
    require(not any("override" in event["event"] for event in events),
            "Token override recorded")
    tokens = [event for event in events if event["event"] == "token"]
    cursor = 0
    verified = []
    for expected, row in zip(manifest["cases"], result["results"], strict=True):
        case = expected["id"]
        require(row["id"] == case, "Case identity or order differs")
        require(row["formatted_prompt_sha256"] == expected["prompt_sha256"]
                == digest(row["formatted_prompt"].encode("utf-8")),
                f"Prompt bytes differ: {case}")
        prompt_ids = row["prompt_token_ids"]
        require(len(prompt_ids) == row["prompt_tokens"] == expected["prompt_tokens"]
                and id_digest(prompt_ids) == expected["prompt_ids_sha256"],
                f"Prompt IDs differ: {case}")
        ids = row["token_ids"]
        pieces = row["token_piece_utf8_hex"]
        require(len(ids) == len(pieces) == row["completion_tokens"] == expected["completion_tokens"]
                and id_digest(ids) == expected["completion_ids_sha256"],
                f"Completion IDs differ: {case}")
        require(row["finish_reason"] == "eog" and ids[-1] == manifest["eog_id"]
                and ids.count(manifest["eog_id"]) == 1
                and bytes.fromhex(pieces[-1]) == b"<|im_end|>",
                f"Natural termination differs: {case}")
        require(len(tokens) - cursor >= len(ids), f"Missing live token events: {case}")
        for step, (token, piece) in enumerate(zip(ids, pieces, strict=True)):
            event = tokens[cursor]
            cursor += 1
            require((event["case_id"], event["step"], event["token_id"],
                     event["piece_utf8_hex"], event["eog"])
                    == (case, step, token, piece, step == len(ids) - 1),
                    f"Raw and live token evidence differ: {case} step {step}")
        whole = b"".join(bytes.fromhex(piece) for piece in pieces[:-1])
        require(digest(whole) == expected["whole_generation_sha256"]
                and whole.count(b"</think>") == 1, f"Generation bytes differ: {case}")
        final = whole.partition(b"</think>")[2]
        require(digest(final) == expected["reviewed_final_sha256"], f"Reviewed proof differs: {case}")
        verified.append({"id": case, "completion_tokens": len(ids), "finish_reason": "eog"})
    require(cursor == len(tokens), "Extra live token events")
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_bytes())
    result = json.loads(args.result.read_bytes())
    require(args.model.resolve(strict=True) == Path(result["model"]).resolve(strict=True),
            "Result model path differs from the file being checked")
    require(checkpoint_digest(args.model) == manifest["checkpoint_sha256"], "Checkpoint SHA-256 differs")
    verified = verify(manifest, result, args.log.read_bytes())
    print(json.dumps({"status": "EXACT_REVIEWED_PROOF_PAIR", "cases": verified}, indent=2))


if __name__ == "__main__":
    main()
