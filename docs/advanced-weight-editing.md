# Direct saved-weight editing: Qwen3.8-27B Abliterated and beyond

This guide develops small, testable changes to **saved model weights**, while preserving the original checkpoint. The motivating local research uses [Huihui-Qwen3.8-27B-abliterated-GGUF](https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF). Its name identifies the artifact; it does not establish a tensor layout, an editing method, or mathematical ability. Inspect the exact file and runtime you actually use.

The repository supplies numerical infrastructure and a synthetic example. It does **not** establish that an edited checkpoint is the best math model, or that a proposed native procedure has already passed. No model weights are redistributed here. Methods below that fit changes to labeled states are **supervised fitting**, including when they use closed-form algebra or avoid backpropagation.

## What the source experiment establishes

The [HN discussion](https://news.ycombinator.com/item?id=50341174) links to the authors' [weight-space programming post](https://rikiyat.github.io/blog/weight-space-programming/). Its math experiment concerns **Qwen3.5-0.8B**, with an activation/forward-pass harness and practice problems. The [pinned experiment README](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/README.md) describes the restrictions, sampling, and BF16 evaluation. It explicitly disallowed output-head and final-normalization edits; the head methods in this guide are different experiments.

The released [final choice](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/runs/p50c/final_answer.md) targets repetitive thinking through selected MLP down-projection columns. Its [manifest](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/runs/p50c/edit/manifest.json) identifies two 1024×3584 tensors, 64 selected columns each, and **130,188 BF16 entries actually changed** after rounding. This distinction between requested and stored changes matters. The [Gemma follow-up](https://github.com/RikiyaT/lm_understand-logs/blob/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f/exp8_math/gemma_followup/README.md) did not establish a math improvement for a model without the same dominant failure. These results do not authorize copying layer numbers, directions, column indices, or doses into another checkpoint.

[ROME](https://arxiv.org/abs/2202.05262v5) studies localized factual associations and rank-one MLP updates, with separate specificity and generalization tests. [MEMIT](https://arxiv.org/abs/2210.07229v2) extends factual editing to many associations across selected layers. Their covariance-weighted preservation objectives are useful background. The finite-guard nullspace construction below is a different constraint, and a complete mathematical derivation is a different target from a subject–relation–object fact.

## Freeze the experiment before fitting

Use distinct names for distinct controls:

| Artifact | Meaning |
|---|---|
| B | Immutable original checkpoint |
| A | Current accepted reference; initially B until a candidate qualifies |
| P | Exact parent of this experiment; it can equal B or be a separately identified earlier edit |
| C | No-edit representation control: for example, the same requantization or promotion as E |
| E | Intended edit applied through that representation path |

Record model repository revision, exact filename, full-file SHA256, tokenizer/template hashes, runtime commit and binary hash, backend, context length, sampling, and seeds. Hash source code, training inputs, labels, gates, and complete-output rubrics. Keep training, development, and untouched evaluation roles explicit. An evaluated case can become training for a later experiment, but it then ceases to be fresh evidence.

Before capturing data, verify tensor name, dimensions, orientation, dtype, block/row size, byte range, and whether input embeddings and the output matrix share storage. A filename such as `IQ3_XXS` does not guarantee every tensor has that dtype. GGUF records per-tensor metadata; its [official header](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/include/gguf.h) describes descriptors, offsets relative to the tensor-data blob, and alignment.

Capture **exact token IDs and the state predicting the next token**. Replay the prefix and check that projected logits agree with native logits. A token index is not a character offset. A preferred digit is not necessarily uniquely correct: different digits can begin equivalent expressions. Validate complete continuations and counterexamples before labeling a state.

## Editing an untied output head

Write the mathematical head as $W\in\mathbb R^{V\times d}$, with final normalized hidden vector $h$ and logits $z=Wh$. This orientation is mathematical; verify how the runtime stores it. For an untied row $t$, replacing $w_t$ with $w_t+\delta$ changes its fixed-prefix logit by $h^\top\delta$. Other row logits remain unchanged at that fixed hidden state. Subsequent generated prefixes can change completely.

For a balanced two-row intervention with preferred token $c$ and alternative $w$:

$$
\Delta w_c=\delta/2,\qquad \Delta w_w=-\delta/2.
$$

Fit inequalities against **both** the other edited token and the maximum over every unchanged vocabulary row. A two-token softmax misses an unchanged token that still wins. Control states must cover all original winner categories: $c$, $w$, and an unchanged token. Define how ties are handled before fitting; rejecting ambiguous cross-category ties is one conservative choice.

Minimum-norm inequality fitting can trade off repair with preserved greedy margins. Keep solver convergence, primal residuals, KKT diagnostics, and each row's relative norm change. A small global fraction of head parameters is not evidence of behavioral locality: an output digit row participates in many contexts.

A closing-token row is a **completion-efficiency** experiment. Verify the exact token is single-token, non-EOG, and handled as expected by the template. Label ready states only after the required endpoint and proof are complete; include unfinished states, self-correction, ordinary prose, and post-thinking states as negatives. Natural closing states can be behavior anchors without being evidence of calibrated proof readiness. Faster closing can suppress a necessary repair or repeat a delimiter. It does not teach a theorem.

## Contextual internal FFN editing

An internal down projection can condition an intervention on its activation. Suppose the verified local computation is

$$
r=s+D a,\qquad D\in\mathbb R^{d\times p}.
$$

Here $a$ is the activation immediately before the down projection, $s$ the residual skip, and $r$ the residual entering the downstream suffix. With

$$
\Delta D=u v^\top,
\qquad \Delta r=u(v^\top a),
$$

the vector $v$ selects contexts and $u$ changes the residual. This can be merged into saved weights; a runtime adapter is not required.

A **terminal** down projection is a useful engineering starting point because the remaining suffix may be only final normalization and the head. The pinned [Qwen35 graph implementation](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/src/models/qwen35.cpp) is one concrete example to inspect, not an architecture contract for future Qwen releases. Verify scales, control vectors, adapters, extra heads, and graph placement in your build. Native captures must establish that, for identical token prefixes, $a$ and upstream cached state are independent of the selected D edit. That shortcut generally fails for an earlier-layer edit with downstream blocks.

### Exact RMS suffix and pair gradient

For a verified ordinary RMSNorm suffix, use the actual epsilon and gamma:

$$
q=\sqrt{r^\top r/d+\epsilon},\qquad h=\gamma\odot r/q.
$$

For two decoded head rows, let $k=\gamma\odot(w_c-w_w)$. Their margin and residual gradient are

$$
m(r)=k^\top r/q,\qquad
\nabla_r m=k/q-r\frac{k^\top r}{d q^3}.
$$

These are exact for the supplied real-arithmetic formula; they are not a promise of native kernel equality. The [runtime graph's normalization code](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/src/llama-graph.cpp) must match the assumed operations. Calibrate native residual, normalized hidden state, decoded head rows, and logits at representative fixed prefixes before fitting.

The [suffix helper](../numerical/suffix_context_math_v8.py) provides this gradient and a bounded one-direction residual step. It can use the gradient's tangent component $g-r(r^\top g)/(r^\top r)$, avoiding a purely radial direction. It freezes a direction, computes the exact RMS margin along it, finds the analytic line peak within a supplied cap, then uses 64 bisections to reach a supplied target when possible. This is a **directional solver**, not a global optimizer. A missed target establishes neither global infeasibility nor a reason to silently increase the cap.

### Project a key away from supplied guards

Let the rows of $A$ be early/control down-input activations and let $a_+$ be a repair activation. Using a thin SVD, retain a numerically defined basis for the row span of A, then compute

$$
b=a_+-\operatorname{proj}_{\operatorname{row}(A)}a_+,
\qquad v=b/(a_+^\top b).
$$

When valid, $a_+^\top v=1$ and $Av\approx0$. Recompute both quantities rather than trusting the algebra. Tiny separation means a huge, fragile key; reject it explicitly. The helper freezes rank tolerance $\epsilon_{64}\max(A.shape)\sigma_{max}$, minimum separation ratio $10^{-3}$, positive-response error $10^{-8}$, and maximum supplied-guard response $10^{-6}$. These are this helper's numerical choices, not universal model-quality thresholds.

It accepts at most 4,096 guards of width 17,408 and avoids a width-square projector. The maximum F64 guard input alone is 544 MiB; thin SVD outputs and workspace add substantial memory. Unload the full model before a large dense projection. Do not drop early prefixes silently to fit the bound. A streamed guard audit can cover more states, but it does not itself solve the larger nullspace problem.

## Sequence objectives and prefix protection

For gold next token $y_i$, full-vocabulary negative log likelihood is

$$
\ell_i=\operatorname{logsumexp}_{j\in\mathcal V}z_{ij}-z_{iy_i}.
$$

Use the full vocabulary, preferably reduced in bounded batches with stable log-sum-exp. A shortlist softmax is a different objective. An internal residual edit changes all logits, so parent log-normalizers cannot be reused for the edited state. The helper accepts actual corresponding full-vocabulary logZ and gold logits; it does not implement a native whole-head replay engine.

Complete correct teacher responses are useful soft targets. Identify hard mathematical spans and allow equivalent derivations; arbitrary prose or one canonical coefficient spelling should not become mathematical truth. Lower teacher-forced NLL does not establish a valid free-running solution.

Preserve the whole early trajectory outside the intended intervention, including spaces, punctuation, numbers, and useful correction steps. At fixed prefixes, measure original all-vocabulary winner retention and frozen margins after materialization. After the first generated divergence, rerun actual generation; old hidden states no longer describe that trajectory. A handful of isolated guarded prefixes cannot certify every intervening token.

## Packed Q4 edits and no-edit controls

The pinned [Q4_K structure](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/src/ggml-common.h) uses 256 decoded weights per 144-byte block: shared FP16 scale fields, packed subgroup scale/min fields, and 128 code bytes. It is not an array of independently stored floats. The [native decoder](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/src/ggml-quants.c) determines value order and rounding. IQ3 and other formats require their own verified handling.

Two distinct experiments are possible:

1. **Requantize selected blocks.** Build C by decoding and re-encoding without an intended edit, and E through the same path with the edit. Preserve untouched block bytes. Report E−P, C−P, and E−C, including off-support decoded drift, norm, alignment with the requested update, and rounded-away changes. Shared quantization metadata can move weights you did not intend to change.
2. **Freeze metadata and edit codes.** Keep block scales/mins byte-identical and change only allowed code nibbles. C can then equal P exactly. Verify every coordinate/code mapping against the actual native decoder. Coordinate-specific lookup tables of its F32 outputs avoid assuming nominal code steps reproduce the decoder bit-for-bit. Bounds such as code distance ≤2 and row norm ≤15% describe a particular frozen experiment, not generally appropriate defaults.

A deterministic greedy discrete solver is a local search. Local stall or exhaustion of a move budget means feasibility is unknown. It is not a global minimum-norm solution. Recheck actual decoded row norms and all native margins before constructing a model candidate; float-fit success cannot replace those checks.

## Promotion-only C versus edited E

When a verified packed grid is unavailable, promote one chosen tensor to F32 in a derivative checkpoint. C contains its **native-dequantized parent values with no fitted change**. This does not recover the original pre-quantization weights. Quantized and F32 matmul paths can also differ with identical decoded coefficients, so measure P→C with ordinary native inference.

For E, materialize in bounded chunks:

$$
D_E=\operatorname{F32}(D_C+UV^\top),\qquad
\Delta D_{actual}=\operatorname{F64}(D_E)-\operatorname{F64}(D_C).
$$

Use actual stored differences for norms and response estimates. The [streaming helper](../numerical/terminal_down_stream_v8.py) uses at most 32 output rows and 128 activation states per batch. Its reference dimensions are 5120×17408, a 340 MiB F32 tensor. It enforces intended and actual matrix updates ≤1% of the control Frobenius norm, plus a ≤5% positive-state residual cap for its F64 stored-weight response calculation. These are bounded experiment gates; they do not imply argmax preservation.

Rounding can destroy context nullity. The synthetic verification demonstrates an intended `[+1,-1]` change becoming actual `[0,-1]`: a guard with zero intended response then receives −1. Recompute $\Delta D_{actual}a$, and subsequently native C/E residuals and logits. F64 multiplication of stored differences does not certify native F32 GEMM reduction behavior.

Changing dtype changes tensor size. A reviewed, model-specific writer must account for descriptors, alignment, all relocated tensor ranges, trailing bytes, and exact untouched payload identity. Re-read physical C/E files and compare their entire non-target complement. **There is no universal GGUF byte-patch recipe in this guide**, and the numerical helper performs no GGUF I/O.

## Reload, evaluate, and retain rollback

Load a fresh runtime context after changing saved weights. Do not reuse a session cache or recurrent/KV state computed by the old checkpoint. The [llama API](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/include/llama.h) exposes memory operations, but cache validity across a custom edit is an architectural proof obligation. Even where head-only or terminal-down independence can be established for identical prefixes, fresh contexts are the straightforward controlled comparison. Never mutate a file currently mapped by the running model.

Grade complete P/C/E answers with equal prompts and budgets. Record endpoint correctness, validity of every displayed equality, domain assumptions, proof completeness, format, completion, and tokens/time separately. A correct box following a false derivative line is an endpoint pass with a derivation defect. A token-cap baseline is censored: an edited completion is a completion rescue, not proof the baseline could never solve it. Lower token counts are useful only alongside preserved mathematical quality; wall time also depends on backend and loading.

Include counterbalanced token contexts, unfinished problems, correction opportunities, unrelated math families, multilingual formulations when relevant, and ordinary code/prose/format regressions. Freeze new evaluation before seeing candidate outputs. Keep held-out material out of public examples and fitting. Broader claims require broader representative evaluation and uncertainty estimates, not one rescued exercise.

Keep B immutable, identify every derivative by hash, and record rejection reasons. Promote a qualifying E only after the stored/native and complete-answer gates, comparison with both immediate experimental P and accepted A, and preservation of accepted fixes. Then use the new A as the next default research parent and refresh its activations/controls. Rejection leaves A unchanged. This is an iterative research policy, not evidence that recursive improvement has already succeeded.

Keep full weights for B, current A, one prior accepted rollback, active P/C/E and any checkpoint an active validator actually reads. Prune older rejected/superseded weights only after checking dependencies; preserve small lineage records and receipts. Use explicit owned, resolved regular files rather than broad recursive deletion. APFS logical sizes do not measure reclaimed space: check actual free space before/after pruning and preflight new allocations. Rollback uses a retained checkpoint and a fresh runtime context; acceptance and activation remain separately recorded actions.

## What has actually been verified here

The bundled numerical checks run without loading a model:

```sh
python numerical/verify_suffix_context_math_v8.py
python numerical/verify_terminal_down_stream_v8.py
```

The suffix receipt records 16 mathematical checks, 11 invalid-input rejections, and maximum all-coordinate gradient finite-difference error **6.745040082023479e−10**. The streaming receipt verifies complete synthetic 340 MiB logical-matrix coverage in bounded chunks, stored-F32 changes, hashes/norms, input guards, and the rounding-leakage example. These are executed synthetic measurements. Native architecture calibration, a production GGUF writer, model-prefix preservation, and math improvements are separate procedures and are not established by these receipts.

| Reviewed source | SHA256 |
|---|---|
| `suffix_context_math_v8.py` | `0cfc8d1b1451cfa9c0ce5eed9223a7302acd2f5568d5a799798af06b121492c9` |
| `terminal_down_stream_v8.py` | `5f936d32eb78903e19f880a31b8ad49c42536eb01f57d539c4a2ad6b860965c3` |

Use the accompanying contracts and receipts for exact numerical assumptions. Recheck source hashes before running. [Primary references and their limits](references.md) identify the source material behind this guide.
