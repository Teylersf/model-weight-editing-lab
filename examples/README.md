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
