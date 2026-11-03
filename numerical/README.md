# Numerical helpers from the Qwen weight-editing experiments

These original NumPy tools are byte-exact copies of the frozen V8 numerical sources used in the local research work. They contain no model parameters, native capture code, file-format writer, or runtime integration.

| File | Purpose |
| --- | --- |
| `suffix_context_math_v8.py` | Learned RMS normalization, selected logits, exact pair-margin gradients, guarded context keys, bounded residual steps, full-logZ NLL. |
| `terminal_down_stream_v8.py` | Chunked rank updates and audits of actual stored F32 differences and supplied activation responses. |
| `verify_suffix_context_math_v8.py` | Small synthetic derivative, projection, and invalid-input checks. |
| `verify_terminal_down_stream_v8.py` | Synthetic full-shape streaming coverage, F32 rounding, guard leakage, and cap checks. |

Run from the repository root:

```bash
python numerical/verify_suffix_context_math_v8.py
python numerical/verify_terminal_down_stream_v8.py
```

The suffix verifier checks 16 mathematical properties and 11 invalid-input cases. The stored historical receipt records the finite-difference errors for its original NumPy environment; new environments may have small numerical differences. The streaming verifier visits a 5120×17408 F32 logical matrix in at most 32-row chunks, and demonstrates that F32 rounding can break an intended exact guard nullity.

The helper contracts specify the experimental bounds and assumptions. Those bounds are not universal model-editing recommendations. A successful numerical audit does not validate a GGUF file, prove native-kernel equivalence, preserve arbitrary generations, or establish mathematical improvement.

Native work still needs actual tensor/graph alignment, a representation-only control, stored-payload and non-target-tensor checks, fresh native inference contexts, full-vocabulary comparisons, and complete-answer evaluation. See [the advanced guide](../docs/advanced-weight-editing.md).
