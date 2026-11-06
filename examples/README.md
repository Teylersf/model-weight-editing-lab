# Run the tiny direct-weight example

Use a Python environment that already has NumPy. The script does not install
anything, download a model, start a service, or touch another checkpoint.

From the project directory:

```sh
python examples/rank_one_head_edit.py --output-dir demo-output
python -m unittest discover -s tests -v
```

`demo-output` must not exist. Pick another name to repeat the run. Omitting
`--output-dir` creates a fresh system temporary directory and prints its path.

The example generates a three-token, four-feature F32 checkpoint locally. Its
files are:

| File | What it contains |
|---|---|
| `parent.npz` | Original toy weights; marked read-only and hashed before/after |
| `candidate.npz` | Directly edited weights, saved and then reloaded |
| `receipt.json` | Actual target/guard/evaluation results, vectors and hashes |

An output head computes `logits = W @ hidden`. A logit is a score; the largest
score wins. A margin is the desired token's score minus the largest alternative.
This example changes the target margin from **−0.75 to +1.0**, while leaving all
scores at two protected guard contexts exactly unchanged.

The edit is `ΔW = u vᵀ`. Vector `v` selects an activation direction and vector
`u` says how each token's score should change when that direction is present.
The script first removes the guard directions from the target, then normalizes
`v` so its response at the target is one. It raises POSITIVE and lowers NEGATIVE
equally. This is a supervised fit to supplied feature vectors, not a new fact
learned by a transformer.

The script checks the **reloaded** candidate rather than trusting the intended
floating-point update. It also checks that the original checkpoint hash is
unchanged. Fixed ZIP timestamps and array order make the toy checkpoint bytes
deterministic for the same arrays.

Three separate evaluation contexts deliberately expose the limitation: one
improves, one regresses, and one keeps the same correct answer. Aggregate accuracy
stays 2/3, which would hide the regression if only the total were reported. These
engineered examples are not a statistical benchmark or evidence of broad model
improvement. Only the supplied guard directions receive the algebraic protection.

The receipt includes a separate scalar uniform-grid rounding demonstration. It
shows a nonzero requested change disappearing after rounding. That grid is
explicitly a toy; it does not implement any real LLM quantization format.

## Verify the Pilot 122 packed query recipes

The read-only verifier checks all eight published recipes and their TSV digests.
Supply the exact Pilot 024 GGUF to hash the full parent and reconstruct every
edited row in memory. It takes Python 3.11 or newer and runs without a GPU.

```sh
python examples/verify_pilot122_query_overlay.py
python examples/verify_pilot122_query_overlay.py --model /path/to/pilot-024.gguf
```

The recipes identify the IQ4_XS code indices, signed changes, and full-row
hashes. [Recipes and measured CUDA screen](../evidence/direct-accuracy-pilot-122-query-overlay.json)

## Replay the Pilot 176 output-scale edit

Use the exact Pilot 024 GGUF with SHA-256
`674c1e84a2adbf0232b6bb3d4d24a4d00f7c60b109d665f3fe5c88a484589db3`.
The verifier streams the checkpoint on CPU and checks the GGUF layout, each
edited row, and both full checkpoint hashes. Omit `--output` for read-only
verification.

```sh
python examples/replay_output_scale_edit.py --parent /path/to/pilot-024.gguf
```

Expect `VERIFIED_ONLY`, 157 binary16 fields across four `output.weight` rows,
166 changed bytes, and candidate SHA-256
`c05db6800071fa61eea09de4e8e270e6aa36126617c88449f2b227f2cfcd4ce8`.
The capsule gives the exact little-endian before and after values for the
`d` and `dmin` fields at offsets 0–3 within their 144-byte Q4_K blocks.
[Pilot 176 patch capsule](../evidence/direct-closure-pilot-176-row-patch.json)

Add `--output /path/to/pilot-176.gguf` to write the verified checkpoint to
a fresh path on a hard-link-capable filesystem with room for the 11.67 GB file.

## Replay the Pilot 194 mixed output edit

Use the exact Pilot 024 GGUF pinned above. The command checks every modified
row and streams both full checkpoint hashes on CPU.

```sh
python examples/replay_output_mixed_edit.py --parent /path/to/pilot-024.gguf
```

Expect `VERIFIED_ONLY`, 158 binary16 fields and 21 four-bit codes across four
output-weight rows, and 186 changed bytes. The exact checkpoint SHA-256 is
`e2bda6ca06e17d74cb46f36cb407fd99035323a297425feba04eb76048ec8d7b`.
[Pilot 194 patch capsule](../evidence/direct-closure-pilot-194-row-patch.json)

Add `--output /path/to/pilot-194.gguf` to write a verified copy to a fresh path
on a hard-link-capable filesystem with room for the 11.67 GB file.

## Replay the Pilot 209 mixed output edit

The same tool accepts the Pilot 209 capsule and the exact Pilot 024 parent.
It verifies both full checkpoint hashes on CPU.

```sh
python examples/replay_output_mixed_edit.py --pilot 209 --parent /path/to/pilot-024.gguf
```

Expect `VERIFIED_ONLY`, 158 binary16 fields and 3,713 code nibbles across four
output-weight rows, and 3,526 changed bytes. The checkpoint SHA-256 is
`312cb0e6998157552106fe9d0089cd3d3fd6f12429759842e1722c0096f807dc`.
[Pilot 209 patch capsule](../evidence/direct-closure-pilot-209-row-patch.json)

Add `--output /path/to/pilot-209.gguf` to write a verified copy to a fresh path.
