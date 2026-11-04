# Numerical helpers from the Qwen weight-editing experiments

The V8 NumPy tools are byte-exact copies of frozen numerical sources from the local research. The rank-two guard projection extracts the numerical functions from the Windows fit driver. These files contain no model parameters, native capture code, file-format writer, or runtime integration.

| File | Purpose |
| --- | --- |
| `suffix_context_math_v8.py` | Learned RMS normalization, selected logits, exact pair-margin gradients, guarded context keys, bounded residual steps, full-logZ NLL. |
| `terminal_down_stream_v8.py` | Chunked rank updates and audits of actual stored F32 differences and supplied activation responses. |
| `verify_suffix_context_math_v8.py` | Small synthetic derivative, projection, and invalid-input checks. |
| `verify_terminal_down_stream_v8.py` | Synthetic full-shape streaming coverage, F32 rounding, guard leakage, and cap checks. |
| `guarded_rank_two_geometry.py` | Pivoted QR for the full guard span and one or two normalized edit keys. |

Run from the repository root:

```bash
python numerical/verify_suffix_context_math_v8.py
python numerical/verify_terminal_down_stream_v8.py
```

The suffix verifier checks 16 mathematical properties and 11 invalid-input cases. The stored historical receipt records the finite-difference errors for its original NumPy environment; new environments may have small numerical differences. The streaming verifier visits a 5120×17408 F32 logical matrix in at most 32-row chunks, and demonstrates that F32 rounding can break an intended exact guard nullity.

With NumPy and SciPy installed, this small example exercises the same projection functions used in the Windows Euler follow-up. Supply guard matrices with one activation per row. The edit keys give unit response on the corresponding target row and zero response on other targets and guards to numerical tolerance.

```python
import numpy as np
from numerical.guarded_rank_two_geometry import geometry

guards = np.array([[1, 0, 0, 0], [2, 0, 0, 0]], dtype=float)
targets = np.array([[3, 1, 0, 0], [4, 0, 1, 0]], dtype=float)
keys, audit = geometry([guards], targets)
assert audit["qualified"]
np.testing.assert_allclose(guards @ keys, 0, atol=1e-12)
np.testing.assert_allclose(targets @ keys, np.eye(2), atol=1e-12)
```

The Windows run used 10,841 guard rows with 17,408 features. It applied the QR reflectors without building a dense orthogonal matrix and rechecked every guard against the returned keys. Matrix change is measured separately after the payload is rounded. The geometry helper does not use a fixed cumulative matrix-change cutoff. [Windows case study](../docs/case-study.md#restoring-the-euler-proof-while-preserving-the-interval-proof)

The helper contracts specify the experimental bounds and assumptions. Those bounds are not universal model-editing recommendations. A successful numerical audit does not validate a GGUF file, prove native-kernel equivalence, preserve arbitrary generations, or establish mathematical improvement.

Native work still needs actual tensor/graph alignment, a representation-only control, stored-payload and non-target-tensor checks, fresh native inference contexts, full-vocabulary comparisons, and complete-answer evaluation. See [the advanced guide](../docs/advanced-weight-editing.md).
