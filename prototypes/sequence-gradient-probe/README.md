# Synthetic packed-head gradient probe

**Status: syntax checked; native execution is UNRUN_NATIVE.** This is a tiny future-method prototype, separate from the Mac's active V10 experiment. It reads no model or GGUF, writes no weights, runs no optimizer and changes no settings or dependencies. No sequence-training or mathematical-answer improvement is established.

`probe.cpp` creates fake F32 head rows, quantizes them to Q4_K, and exercises a CPU forward and the public packed-head `OUT_PROD` pullback. There are 3 synthetic positions, a 17-token fake vocabulary, hidden width 256, input width 7 and rank 2. This is the entire tiny vocabulary, not a shortlist approximation to Qwen's vocabulary.

The host computes

```
q = A V^T
r = base_r + q U^T
h = gamma * r / sqrt(mean(r^2) + epsilon)
delta = (softmax(native_CPU_logits) - one_hot(target)) / batch
g_h = OUT_PROD(packed_head, transpose(delta))
g_r = gamma*g_h/s - r*sum(gamma*g_h*r)/(hidden*s^3)
g_U = g_r^T q
g_V = (g_r U)^T A
```

Only the head pullback is a native backward operation here. RMS and factor pullbacks use explicit host F64 algebra. F32 fixture values are evaluated in F64 for the factor/RMS calculation; hidden activations and the native logit cotangent are rounded to F32 at the graph inputs. The native input and output are both bounded tiny arrays.

## What the two checks mean

The pinned CPU forward uses a Q8_K activation dot type for Q4_K weights. Its quantization includes rounding and data-dependent scales. The decoded-weight pullback is therefore a **surrogate**, not the exact derivative of this native quantized forward. [Pinned CPU type traits](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/src/ggml-cpu/ggml-cpu.c), [packed OUT_PROD implementation](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/src/ggml-cpu/ops.cpp).

`reference.py` independently checks differentiable decoded-linear mean cross entropy, and also the decoded pullback with a fixed cotangent taken from the native logits. It compares native `OUT_PROD` against the directly decoded packed rows, then checks the RMS/factor chain separately. Central differences of the **actual quantized CPU mean CE** over five step sizes are retained as diagnostics; matching those differences is not a gradient acceptance condition.

The pure NumPy reference has passed 30 directional checks, maximum absolute finite-difference error about `4e-10`. Negative controls reject omission of the RMS radial term and omission of batch averaging. Its self-test uses a deterministic synthetic grid, **not a Q4 encoder**. See `pure-reference-receipt.json`. Native fixture checking alone cannot attest that a fixture was actually produced by a particular binary.

## Build and run later

The four headers in `api/` are byte-pinned to llama.cpp commit `8642541b255bfb5dc39cd351a178be09013a55d6`; `api-source-pins.json` records their official source URLs and SHA256 values. Their MIT notice is in `api/UPSTREAM-LICENSE.txt`. The C++ source passed MSVC C++17 `/W4 /Zs` with zero warnings. **That generated no executable and did not test a native kernel.** No matching GGML library set was available and validated in this Windows task workspace.

On the Mac, use the already installed, separately identity-verified CPU/base/GGML libraries from the same pinned build. Do not install packages or change the active research environment to run this probe. For example, after substituting the verified library directory:

```sh
c++ -O2 -std=c++17 -Iapi probe.cpp -L/verified/ggml/lib \
  -Wl,-rpath,/verified/ggml/lib -lggml-cpu -lggml -lggml-base -o synthetic-gradient-probe
( set -C; ./synthetic-gradient-probe > native-fixture.json 2> native-stderr.log )
python3 -B reference.py --native-json native-fixture.json --receipt native-reference-check.json
```

The binary accepts no arguments or input paths. It uses CPU reference mode and 2 threads. Tensor allocation is capped at 16 MiB, context metadata is 2 MiB, and peak process RSS is reported and capped at 256 MiB where `getrusage` is available. Its sole output is JSON on stdout; diagnostics use stderr. An unsupported operation or failed numerical check exits with failure. Use a fresh output/receipt name so an existing observation is not overwritten.

Record compiler flags, source/header hashes, library identities before/after, return codes, raw stdout/stderr and the reference receipt when it is eventually executed. The compile-time expected commit printed in JSON does not independently verify the linked binary's source provenance. At the recorded source freeze, this prototype had not been run on the Mac. Native execution remains unverified in this distribution; any later scheduling must preserve active experiment timing and runtime ownership.

## Remaining work

- Execute against the verified native library set and check the emitted fixture with the independent reference.
- Measure exact backend/precision differences before composing a real suffix trainer; no Metal backward equivalence is claimed.
- For real training, separately validate teacher-forced prefixes, data roles, full-vocabulary objectives, serialized F32 merge rounding, native preservation, and complete mathematical answers.

These files are a synthetic implementation probe. They are not an approval gate or a reason to hold the current numerical experiment.

## Public package provenance and license

[`freeze.json`](freeze.json) is this public distribution manifest. Source, reference, the pure-reference receipt, API pins, four headers and upstream license are byte-exact copies of the audited originals. [`readiness.json`](readiness.json) and [`independent-source-review.json`](independent-source-review.json) are explicitly labeled public derivatives: absolute machine paths were removed, and the public source-review hash was updated. Their original private hashes and the original private freeze hash remain provenance records; the original private receipt/freeze bytes are not distributed, and their old pins do not identify the redacted files. This README is also a public derivative. No test or native run was repeated for packaging.

The original probe/reference code and this documentation use the repository's [MIT license](../../LICENSE). The four vendored GGML headers retain their separate [upstream MIT notice](api/UPSTREAM-LICENSE.txt), copyright 2023-2026 The ggml authors, and [pinned primary-source locations](api-source-pins.json). No model weights, native libraries, executables, private prompts or model outputs are included.
