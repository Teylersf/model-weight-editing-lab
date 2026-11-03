# Model Weight Editing Lab

An AI model stores much of what it has learned in **weights**: arrays of numbers used to turn an input into an output. Editing weights means changing those saved numbers, loading the changed model, and measuring what its behavior actually does.

**We are directly editing the saved weights of Qwen3.8-27B Abliterated on a local Mac.** Our goal is faster, more reliable high school and college mathematics, including reducing unproductive thinking loops. This repository explains the process from a small example you can run on an ordinary computer to the equations, quantization issues, and native-runtime checks needed for a large model.

The experiments are ongoing. Some edits changed the intended behavior; some passed local checks and failed during complete answers. We have **not** established a generally improved math model or a state-of-the-art result. Those failures are part of the guide.

By [Taylor Kalin](https://github.com/Teylersf), with AI-assisted implementation, mathematical checking, and documentation. Independent checking here means separate computational or agent checks, not human peer review.

## Start here: what are we changing?

Think of a language model as a large calculation. It turns text into tokens, builds an internal representation of the context, and calculates a score for each possible next token. Those scores are called **logits**. A decoder chooses a token from them, adds it to the text, and repeats.

A weight matrix is one of the tables of numbers used in that calculation. Changing a matrix can change a token's score, an internal representation, or both. A small change in scores can change a token. That token then changes the context for every following step.

There is no single “be better at calculus” switch. The same weights participate in many tasks. A successful edit needs evidence that the desired behavior improved and other useful behavior survived.

| Term | What it means |
| --- | --- |
| Checkpoint | The saved model parameters and associated configuration. |
| Weight | A learned numeric parameter in the model. |
| Activation | A temporary value computed for a particular input. |
| Token | A unit of text chosen by the model's tokenizer; it is not necessarily a word. |
| Logit | A next-token score before conversion to probabilities. |
| Output head | The matrix that maps the final hidden representation to token scores. |
| Residual | The internal vector updated as information passes through a transformer. |
| Quantization | A compressed numeric representation of weights. |
| Guard | A supplied context whose behavior an experiment tries to preserve. |
| Rank-one edit | A matrix update built from the outer product of two vectors. |

### How this relates to other ways of changing a model

| Approach | What changes |
| --- | --- |
| Prompting | Input text or instructions. |
| RAG | Documents retrieved and supplied as context. |
| Activation steering | Temporary internal values during inference. |
| Fine-tuning | Saved parameters, usually through repeated optimization steps. |
| LoRA | A learned low-rank update, often kept as an adapter and optionally merged. |
| Direct weight editing | Selected saved parameters through an explicit editing procedure. |

These categories overlap. Fine-tuning also edits weights. A low-rank update can be merged into a checkpoint. The important questions are **which values changed, how the change was selected, and what evaluation supports it**.

“Abliterated” describes the upstream model variant we started with. Our current experiment targets math behavior and looping; the name does not establish mathematical accuracy. See the [upstream model card](https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF) for that distribution's description and license.

## Run your first saved-weight edit

The teaching example generates a tiny numeric model locally. It needs no downloaded checkpoint, GPU, model account, or API key. It **does not run or emulate the 27B model**; it makes the editing and verification steps small enough to inspect.

Use Python 3.11 or newer and NumPy. From a terminal:

```bash
git clone https://github.com/Teylersf/model-weight-editing-lab.git
cd model-weight-editing-lab
python -m venv .venv
```

Activate the environment on macOS/Linux:

```bash
source .venv/bin/activate
```

Or on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then:

```bash
python -m pip install -r requirements.txt
python examples/rank_one_head_edit.py --output-dir runs/first-edit
python -m unittest discover -s tests -v
```

Use a fresh output directory for each run. The example refuses to overwrite an existing directory. You can omit `--output-dir` to use a fresh temporary directory.

The example:

1. Creates and hashes a parent checkpoint.
2. Selects one target context and two protected contexts.
3. Calculates a rank-one update.
4. Writes a separate candidate checkpoint.
5. Reloads the candidate and measures its **stored** weights.
6. Checks the target, protected contexts, and separate illustrative evaluation contexts.
7. Writes a machine-readable receipt.

The example deliberately includes an evaluation regression. Its target improves while another context gets worse. It teaches how an edit can work locally without making a model generally better.

## Understand the edit

Suppose the final hidden representation is a column vector $h$ of length $d$. The output head is a matrix $W$ with one row per token:

$$
z = Wh, \qquad W\in\mathbb{R}^{V\times d}.
$$

Here $V$ is the vocabulary size and $z$ contains the logits. We omit a bias for this example; include it when an actual architecture has one.

For a fixed hidden representation, changing output row $w_i$ by $\Delta w_i$ changes that token's logit by:

$$
\Delta z_i = \Delta w_i^T h.
$$

That is why a head edit is a useful starting point: for the **same fixed token prefix**, its immediate logit effect is easy to calculate. Its effect on a whole generated answer is much harder to predict.

### Protect supplied contexts

Let $h_{\star}$ be the target representation. Put protected representations into the rows of a matrix $A$. Remove from $h_{\star}$ the component in the row span of $A$:

$$
q = h_{\star} - \operatorname{proj}_{\operatorname{row}(A)}h_{\star}.
$$

If $q$ is sufficiently nonzero, define:

$$
v = \frac{q}{h_{\star}^Tq}.
$$

In exact arithmetic, $Av=0$ and $h_{\star}^Tv=1$. An update $\Delta W=uv^T$ therefore has the requested effect $u$ at the target and zero effect at the supplied guards.

For two output tokens, choose $u_+=m/2$ and $u_-=-m/2$, with other entries zero. Their **pairwise** margin increases by $m$ at the target. This alone does not establish an all-vocabulary winner: another token might still score higher.

Use an SVD or a suitable linear solve rather than explicitly constructing a huge square projector. If the target is in the protected span, or almost in it, this construction cannot provide a robust selective edit. Record that failure and change the experiment design.

Guards protect only the supplied activations under the assumptions used in the calculation. They do not guarantee preservation of unseen contexts, changed trajectories, or rounded checkpoint values.

## The complete workflow for a real model

### 1. Preserve and identify the parent

Keep the source checkpoint immutable. Write candidates to separate files. Record its repository, revision, filename, byte count, full SHA-256, tokenizer, chat template, runtime commit, and decoding parameters.

Hash a checkpoint on macOS:

```bash
shasum -a 256 /path/to/parent.gguf
```

Or on Windows PowerShell:

```powershell
Get-FileHash -LiteralPath 'D:\Models\parent.gguf' -Algorithm SHA256
```

Names are insufficient identifiers. Different quantizations and revisions can share the same model family name. A whole-file label such as “IQ3” does not mean every tensor inside uses that encoding.

### 2. Define the behavior and score it before editing

For a looping problem, record completion rate, generation length, wall time, repeated reconsideration, answer accuracy, and accuracy of the displayed working. A shorter incorrect answer fails.

Freeze a small experiment plan before fitting: target behavior, allowed tensors, update method, numerical limits, protected contexts, baseline settings, and rejection criteria. Separate three datasets:

- **Training:** prompts, activations, corrections, and feedback allowed to select the edit.
- **Development:** material used to compare experiment designs and diagnose failures.
- **Held-out evaluation:** unseen material reserved for the final claim.

Once you use a failure to choose another edit, it is no longer an untouched test. Relabel it and obtain fresh evaluation material. Repeatedly optimizing against a public math benchmark also risks overfitting that benchmark.

### 3. Reproduce the parent failure

Run ordinary generation with a pinned tokenizer, exact prompt/template, context size, decoding settings, and runtime. Save the generated token IDs as well as text. Reproduce the behavior before trying to repair it.

During controlled comparisons, keep the prompt and sampling settings fixed. A new instruction to “answer quickly” can be useful separately, but cannot establish that a weight edit caused an improvement.

### 4. Trace the actual calculation

Capture the exact tensors consumed by the selected operation. For an output-head edit, capture its actual input $h$. For an internal down-projection edit, capture that matrix operation's actual input $a$, its residual skip input, and the downstream normalized representation.

Check shapes, orientation, dtype, graph connections, normalization parameters, and runtime transformations. A similarly named tensor is not enough. Compare reconstructed values with native runtime outputs before fitting.

Teacher-forced replay feeds an archived token sequence through the model. It provides comparable fixed prefixes. It is useful for fitting and diagnosis, but it does not show what the edited model will choose during free generation.

### 5. Calculate an edit with explicit limits

Start with the narrowest mechanism supported by the trace. A head edit changes token scores directly. An internal feed-forward edit can be context dependent but changes the final representation and therefore potentially **every** output score.

Specify the matrix norm limit and any per-context residual-shift limit before fitting. These are engineering limits for an experiment, not universal thresholds for a safe or effective model.

Use complete correct continuations and mathematically meaningful spans. A single changed digit is not a repaired derivative, proof, or algorithm. Do not confuse a preference for one prose wording with mathematical correctness.

### 6. Materialize, reload, and measure the stored change

Write the candidate, reload it, and calculate:

$$
\Delta W_{\mathrm{stored}} = W_{\mathrm{candidate}}-W_{\mathrm{control}}.
$$

Use this difference for norms and response checks. A float proposal that passes its constraints can fail after F32 rounding or quantization. Record intended and actual changes separately.

For GGUF, use a format-aware implementation. Tensor encodings, block sizes, alignment, descriptors, and offsets matter. This repository does not provide a universal binary patcher for arbitrary GGUF files.

### 7. Separate representation changes from learned changes

When promoting a quantized tensor to a float representation, compare:

| Label | Meaning | Comparison |
| --- | --- | --- |
| P | Pinned parent checkpoint. | Original reference. |
| C | Promotion-only control: same decoded tensor values in the new representation. | P→C measures the representation/kernel change. |
| E | Edited checkpoint with the same representation as C. | C→E measures the additional edit. |

Even with equivalent decoded values, native kernels can produce different results. Run an ordinary baseline for C. Do not attribute P→E differences entirely to the learned update.

### 8. Replay all relevant prefixes and generate fresh answers

An edit can change token 12 even when its intended target is token 2730. Capture the earlier trajectory, inspect margins, and find the first natural divergence.

Check all-vocabulary competitors, protected contexts, complete answers, and format requirements. Start fresh inference contexts when comparing checkpoint versions. Reusing stale KV or recurrent state across changed weights is generally invalid unless the chosen architecture and edit have a specifically established independence argument.

For mathematics, verify the domain, intermediate equalities, final result, and required conditions. For an ODE, substitute into the equation and check the initial values. For linear algebra, check residuals. For proofs, validate the logical steps. For numerical work, use the problem's precision and tolerance requirements.

### 9. Keep or reject the candidate using the frozen criteria

A successful load proves file/runtime compatibility. A passed saved-prefix test proves a local property. A few solved questions give limited behavioral evidence. None establishes broad superiority.

Reject a candidate if it improves stopping while degrading correctness, introduces false equations, or moves the looping problem elsewhere. Preserve a rejected experiment's receipt so the next attempt can address its actual failure.

## Our Qwen3.8-27B Abliterated experiment

The local checkpoint is from [huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF](https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF). Our pinned artifact is:

```text
Huihui-Qwen3.8-27B-abliterated-UD-DW-IQ3_XXS.gguf
11,367,766,944 bytes
SHA-256: bfc6892863eceb16f69697e59b038acdc1c709b790c1542e4612dbb0924d3568
```

The lab uses an M4 Mac with 16 GB of unified memory and a pinned llama.cpp build. The original checkpoint and the existing coding application's settings are preserved. We create separate candidate files containing real saved-weight changes; the native inference tests load those files. No model weights are distributed in this repository.

| Experiment | Observed behavior | Assessment |
| --- | --- | --- |
| V5, a closing-token output-row edit | One proof completed in 679 tokens versus 2,118 for the original. An Euler problem still contained a false displayed derivative despite a correct final solution. | Limited behavior change; not accepted as a general math improvement. |
| V6, a paired digit-row float edit | Intended float checks passed; the packed Q4 representation failed its correction/guard checks. | Rejected before candidate GGUF creation. |
| V7, direct packed-code edits | 45 saved-prefix checks passed. Normal generation first diverged at token 12, and the Euler answer contained false working. A linear-system response used 655 more tokens than V5. | Rejected as a math improvement. |
| V8, internal terminal feed-forward edit | Numerical helpers and initial tracing/calibration prepared; further native control and candidate validation are ongoing. | Experimental, with no accepted model-quality result. |

These are selected lab observations, not a benchmark leaderboard or a general speed guarantee. See the [case study](docs/case-study.md) and [public experiment summary](evidence/experiment-summary.json) for definitions, provenance, and limitations.

### Why we are moving inside the network

In this checkpoint, the terminal feed-forward down-projection is `blk.63.ffn_down.weight`. Its mathematical shape is `[5120, 17408]`, while the GGML dimension listing is `[17408, 5120]`. The native stored tensor is Q4_K even though the checkpoint filename includes IQ3.

We are investigating a merged internal update:

$$
D_E = \operatorname{F32}(D_C + UV^T), \qquad
\Delta r = (D_E-D_C)a.
$$

This is an in-progress method, not a proven repair. The current experiment's limits include rank at most 8, a 1% Frobenius norm budget, a 5% positive-context residual-shift budget, and stored-weight/native checks. The tensor alone occupies 356,515,840 bytes in F32; promoting the entire model is unnecessary for this specific experiment. Memory is still needed for the rest of inference, caches, and fitting.

## Go deeper

- [Advanced weight editing](docs/advanced-weight-editing.md): exact RMS derivatives, internal edits, guard projections, full-vocabulary likelihood, quantization, and native checks.
- [Case study](docs/case-study.md): the actual Qwen experiments and why promising local tests were insufficient.
- [Primary references](docs/references.md): the motivating research, related editing methods, and runtime formats.
- [Numerical tools](numerical/README.md): the bounded NumPy helpers used in this research and their synthetic verification.
- [Contributing](CONTRIBUTING.md): how to report an edit so others can assess it.

Run the numerical checks separately:

```bash
python numerical/verify_suffix_context_math_v8.py
python numerical/verify_terminal_down_stream_v8.py
```

The second check streams a synthetic 340 MiB logical matrix in small chunks. It does not allocate a full 27B model or test that model's mathematical ability.

## Common mistakes

| Mistake | Better check |
| --- | --- |
| “The answer is shorter, so the loop is fixed.” | Check correctness, displayed working, completion, and regressions together. |
| “The target logit increased.” | Check its margin against every relevant competitor. |
| “All saved states passed.” | Replay early prefixes and run full ordinary generation. |
| “The float update passed.” | Re-decode or reload the actual stored candidate. |
| “The guard projection is zero.” | Measure stored-weight leakage and native inference effects. |
| “Promoting Q4 to F32 preserves behavior.” | Run a separate promotion-only control. |
| “This token ID means the same thing in every model.” | Resolve IDs with the pinned tokenizer and template. |
| “The boxed answer is right.” | Check every asserted mathematical step used to support it. |
| “We tested on a public benchmark repeatedly.” | Disclose that feedback and evaluate on fresh material. |

## Share a result others can inspect

Publish a model card or experiment report containing the parent identity, exact changed tensors, update procedure, training/dev/test boundaries, actual serialized delta, native settings, complete-answer rubric, failed cases, and reproduction commands. Keep the original model's licensing and redistribution terms separate from the license for your own code.

This repository uses the [MIT license](LICENSE) for its original code and documentation. Upstream model weights, datasets, and referenced projects retain their own terms. This release contains educational code, numerical infrastructure, and a research report; it contains no trained model release or private evaluation set.
