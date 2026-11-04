#!/usr/bin/env python3
"""Prepare and grade the official MMLU high-school and college mathematics subsets."""
import argparse
import csv
from hashlib import sha256
from io import StringIO
import json
import math
from pathlib import Path
import re
import tarfile


ARCHIVE_BYTES = 166184960
ARCHIVE_SHA = "bec563ba4bac1d6aaf04141cd7d1605d7a5ca833e38f994051e818489592989b"
ARCHIVE_URL = "https://people.eecs.berkeley.edu/~hendrycks/data.tar"
PROTOCOL = "https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/evaluate.py"
SUBJECTS = ("high_school_mathematics", "college_mathematics")
EXPECTED = dict(zip(SUBJECTS, (270, 100), strict=True))
CHOICES = "ABCD"
DATA = {
    "data/dev/high_school_mathematics_dev.csv": (1168, "d7401d5cbad5ae697bfa480e35d85de8ebf1232589a3c59b010782ee49cbe18c"),
    "data/test/high_school_mathematics_test.csv": (48584, "fe8f7a154834bba30947401ba37ea6c7afdcfba82ddc341c79b5d3016991d290"),
    "data/dev/college_mathematics_dev.csv": (1366, "27731ee1402e720ee01ad6fa6a969a0d0978a0e9b4c385d328a61869a43f321f"),
    "data/test/college_mathematics_test.csv": (22429, "8b5bef14d4209c7918eaf947e4f12a5ae9470567722d8ba9761302d733e8ac71"),
}
METHOD = "original-five-shot-raw-mmlu-prompt-full-vocabulary-next-answer-token-argmax"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def archive_ref(path):
    with path.open("rb") as stream:
        size = path.stat().st_size
        result = sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    require(size == ARCHIVE_BYTES and result.hexdigest() == ARCHIVE_SHA, "Official archive SHA-256 or size differs")
    return dict(url=ARCHIVE_URL, bytes=size, sha256=result.hexdigest())


def read_dataset(path):
    archive = archive_ref(path)
    selected = {}
    with tarfile.open(path, mode="r:") as tar:
        for member in tar:
            if member.name not in DATA:
                continue
            extent, pin = DATA[member.name]
            require(member.isfile() and member.size == extent and member.name not in selected,
                    "Official CSV member extent or uniqueness differs")
            with tar.extractfile(member) as stream:
                raw = stream.read()
            require(len(raw) == extent and digest(raw) == pin, "Official CSV SHA-256 differs")
            rows = list(csv.reader(StringIO(raw.decode("utf-8"), newline=""), strict=True))
            require(all(len(row) == 6 and len(row[5]) == 1 and row[5] in CHOICES for row in rows),
                    "Official CSV row contract differs")
            selected[member.name] = rows
    require(set(selected) == set(DATA), "All four official CSV members are required")
    examples = {}
    for subject in SUBJECTS:
        dev = selected[f"data/dev/{subject}_dev.csv"]
        test = selected[f"data/test/{subject}_test.csv"]
        require(len(dev) == 5 and len(test) == EXPECTED[subject], "Official subject split count differs")
        examples[subject] = (dev, test)
    return archive, examples


def format_row(row, include_answer):
    text = row[0] + "".join(f"\n{choice}. {value}" for choice, value in zip(CHOICES, row[1:5], strict=True))
    return text + "\nAnswer:" + (f" {row[5]}\n\n" if include_answer else "")


def prompts(examples):
    for subject, (dev, test) in examples.items():
        # The author evaluator leaves two spaces between "about" and the subject.
        prefix = f"The following are multiple choice questions (with answers) about  {subject.replace('_', ' ')}.\n\n"
        prefix += "".join(format_row(row, include_answer=True) for row in dev)
        for index, row in enumerate(test):
            ident = f"{subject}-{index:03d}"
            yield ident, subject, index, (prefix + format_row(row, include_answer=False)).encode("utf-8"), row[5]


def dataset_contract(archive):
    return dict(archive=archive, author_evaluator=PROTOCOL,
                csv_members={name: dict(bytes=extent, sha256=pin) for name, (extent, pin) in DATA.items()},
                subjects=EXPECTED, split="test", dev_examples_per_subject=5)


def write_bytes(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def write_json(path, value):
    write_bytes(path, (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8"))


def plan_for(archive, examples):
    return dict(schema="standalone-mmlu-official-math-preparation-v1", method=METHOD,
                benchmark=dataset_contract(archive), prompts=[
                    dict(id=ident, subject=subject, row_index=index, prompt_sha256=digest(prompt), prompt_bytes=len(prompt))
                    for ident, subject, index, prompt, _ in prompts(examples)])


def prepare(archive, examples, output):
    output = output.resolve()
    output.mkdir(exist_ok=False)
    prompt_dir = output / "prompts"
    prompt_dir.mkdir()
    lines = []
    for ident, _, _, prompt, _ in prompts(examples):
        path = prompt_dir / (ident + ".utf8")
        write_bytes(path, prompt)
        lines.append(f"{ident}\t{path}\n")
    write_bytes(output / "native-manifest.tsv", "".join(lines).encode("utf-8"))
    write_json(output / "preparation.json", plan_for(archive, examples))


def grade(archive, examples, plan_path, native_path, log_path, output):
    plan = json.loads(plan_path.read_bytes())
    require(plan == plan_for(archive, examples), "Frozen prompt declarations differ from the original splits")
    raw_bytes = native_path.read_bytes()
    live = log_path.read_bytes()
    raw = json.loads(raw_bytes)
    require(raw["schema"] == "windows-mmlu-next-choice-logits-v1" and raw["backend"] == "CUDA0"
            and raw["llama_build"] == "8642541b2" and raw["choice_pieces"] == [" A", " B", " C", " D"]
            and len(set(raw["choice_token_ids"])) == len(raw["choice_token_ids"]) == 4
            and all(type(token) is int and 0 <= token < 248320 for token in raw["choice_token_ids"])
            and raw["context"] == 4096 and raw["batch"] == 64 and raw["threads"] == 4
            and raw["generation_tokens"] == 0 and raw["prompt_token_cap"] == 2048
            and re.search(rb"offloaded\s+66/66\s+layers to GPU", live),
            "Native choice-logit or CUDA placement contract differs")
    events = [json.loads(line[8:]) for line in live.splitlines() if line.startswith(b"WR_LIVE ")]
    event_rows = [event for event in events if event["event"] == "mmlu_case_complete"]
    require(events and events[-1]["event"] == "run_complete"
            and events[-1]["completed_prompts"] == len(raw["rows"]) == len(event_rows) == sum(EXPECTED.values()),
            "Every full test-set row must have native output")
    rows = []
    for step, (source, native, event) in enumerate(zip(prompts(examples), raw["rows"], event_rows, strict=True), 1):
        ident, subject, _, prompt, gold = source
        tokens = native["prompt_tokens"]
        status = native["status"]
        logits = native["choice_logits"]
        require(native["id"] == event["case_id"] == ident and native["prompt_sha256"] == digest(prompt)
                and event["step"] == step and status == event["status"] and tokens == event["prompt_tokens"]
                and native["elapsed_ms"] == event["elapsed_ms"] and math.isfinite(native["elapsed_ms"])
                and native["elapsed_ms"] >= 0, "Exact native/live row identity differs")
        prediction, tie = None, False
        if status == "scored":
            require(0 < tokens <= 2048 and len(logits) == 4 and all(math.isfinite(value) for value in logits),
                    "Scored row has invalid token count or logits")
            top = max(logits)
            prediction, tie = CHOICES[logits.index(top)], logits.count(top) > 1
        else:
            allowed = {"invalid_empty_tokenization": tokens == 0, "censored_prompt_token_cap": tokens > 2048,
                       "invalid_answer_token_boundary": 0 < tokens <= 2048, "invalid_choice_logits": 0 < tokens <= 2048}
            require(status in allowed and allowed[status] and logits == [], "Unexpected unscored row")
        rows.append(dict(subject=subject, status=status, correct=prediction == gold, tied=tie))
    scores = {}
    for subject in (*SUBJECTS, "combined_micro"):
        group = rows if subject == "combined_micro" else [row for row in rows if row["subject"] == subject]
        total = sum(EXPECTED.values()) if subject == "combined_micro" else EXPECTED[subject]
        require(len(group) == total, "Wrong full test-set denominator")
        correct = sum(row["correct"] for row in group)
        scored = sum(row["status"] == "scored" for row in group)
        invalid = sum(row["status"].startswith("invalid_") for row in group)
        censored = sum(row["status"].startswith("censored_") for row in group)
        require(scored + invalid + censored == total, "Unaccounted row status")
        scores[subject] = dict(total=total, correct=correct, scored=scored, scored_wrong=scored-correct,
            invalid=invalid, censored=censored, ties=sum(row["tied"] for row in group), full_split_accuracy=correct/total)
    receipt = dict(schema="standalone-mmlu-official-math-scores-v1", method=METHOD, benchmark=plan["benchmark"],
                   scores=scores, preparation_sha256=digest(plan_path.read_bytes()), native_scores_sha256=digest(raw_bytes),
                   native_log_sha256=digest(live), training_data_overlap_unknown=True)
    write_json(output, receipt)
    print(json.dumps(scores, indent=2, allow_nan=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--archive", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    scoring = sub.add_parser("grade")
    scoring.add_argument("--archive", type=Path, required=True)
    scoring.add_argument("--preparation", type=Path, required=True)
    scoring.add_argument("--native", type=Path, required=True)
    scoring.add_argument("--native-log", type=Path, required=True)
    scoring.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    archive, examples = read_dataset(args.archive)
    if args.mode == "prepare":
        prepare(archive, examples, args.output)
    else:
        grade(archive, examples, args.preparation, args.native, args.native_log, args.output)


if __name__ == "__main__":
    main()
