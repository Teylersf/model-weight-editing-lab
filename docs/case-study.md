# Case study: direct saved-weight edits of Qwen3.8-27B Abliterated

**Research snapshot: 2026-11-03. Project lead: Taylor Kalin.** OpenAI Codex and AI assistants helped develop tooling, check mathematics, and write documentation. The results below distinguish recorded behavior from demonstrated mathematical improvement.

These experiments changed actual saved GGUF weights of **Qwen3.8-27B Abliterated**. The local snapshot was `Huihui-Qwen3.8-27B-abliterated-UD-DW-IQ3_XXS.gguf`, from the [publisher's pinned GGUF repository](https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF/tree/1c69098e9c32db6dc06fc48f1d6cc75ad07da89e). Its verified original SHA-256 was `bfc6892863eceb16f69697e59b038acdc1c709b790c1542e4612dbb0924d3568`. This identifies the specific lab artifact; other conversions and revisions can differ.

The aim was faster, decisive school and university mathematics with correct complete solutions. The base remained immutable while separate candidate files were evaluated. There is no accepted “best mathematics model” result in this snapshot.

## Reading the evidence

**B** denotes the preserved original baseline. **A** is now V10, the provisional accepted research base for the tested scope. **P** is the experimental V5 candidate used as the parent through V9; P and V9 were not accepted improvements. V10 was derived from the unaccepted V9 branch; its previous accepted reference was B, a different checkpoint from its immediate experimental parent. **C** denotes a no-edit representation or packing control where needed; **E** denotes an edited candidate. A changed file, a successful numerical fit, a passed saved-prefix check, and an improved complete answer are four different observations.

The published source of run observations is the [curated experiment summary](../evidence/experiment-summary.json). It records artifact hashes and the limits of what is distributed. Historical helper receipts such as `completion-inequality-fit-verification.json`, `paired-readout-fit-verification.json`, and `q4-discrete-optimizer-v7-verification.json` were inspected locally but are not bundled here. They identify synthetic numerical checks, which do not independently reproduce the Mac model runs. Native checkpoints, raw generations, and capture caches are also not distributed; a hash cannot replace those missing bytes. The mathematical checks below verify the stated solution and particular displayed errors, rather than claiming an audit of every generated token. Only aggregate measurements and selected mathematical equations are presented here.

## V5: shorter answers did not guarantee correct working

V5 edited the untied output row that influences closing a thinking segment. Training prefixes distinguished mathematically ready states, unfinished states, and already-correct natural closing behavior.

| DEV case | Baseline | V5 observation | Mathematical assessment |
|---|---|---|---|
| Finite quotient ring | 2,118 generated tokens | 679 tokens | Correct result and valid presented argument. |
| Cauchy–Euler initial-value problem | No paired completed B cost is supplied in the public summary | 2,952 tokens | Correct final function, but a false displayed derivative equation. |

These counts belong to those particular prompts. The finite-ring reduction was real on that case. For Euler, the public summary supplies V5/V7 totals but no completed original-B length, so it does not establish a paired B-to-V5 full-output speedup.

The Euler endpoint was

$$
y(t)=t^2\left(1-2\ln t+\frac{(\ln t)^3}{6}\right),\qquad t>0.
$$

It satisfies the equation and initial conditions, yet an intermediate product-rule line was wrong. Checking only the boxed answer would have missed that defect.

## V6: a floating-point fit did not survive packing

V6 attempted a targeted edit of numeric-token output rows. The proposed floating-point update and its packed low-bit representation were checked separately. The packed edit failed the intended native-prefix checks and was rejected.

This matters because low-bit packing can alter the realized update. A feasible floating-point constraint system does not prove that the stored candidate satisfies those constraints. Synthetic solver tests, quantizer checks, actual decoded differences, and native logits need separate evidence. This phase supplies no accepted mathematical improvement.

## V7: saved-prefix success did not protect a complete rollout

V7 searched the fixed Q4_K code grid for two output rows while preserving their packing metadata. Its 45 saved-prefix checks passed, but fresh generation reportedly diverged at zero-based generated-token index 12, much earlier than the intended late repair position.

A saved prefix fixes the model's context. In a fresh rollout, an earlier changed token creates a different context and different activations. The original saved-prefix constraints do not automatically cover that new trajectory.

On Euler, V7 generated 1,980 tokens versus P's 2,952. Its thinking-closing token was at zero-based index 716 (the 717th generated token). The final function was again correct, but the displayed working contained several false equations: incorrect particular-solution derivatives, an incorrect operator calculation, and a later incorrect general derivative. A valid second method did not make those earlier claims true. Other full-output checks also reported formatting/loop regressions. Faster output therefore did not meet the unchanged clean-working criterion.

## V8: an internal edit passed preservation but missed the margin gate

V8 saved a rank-one update to the terminal feed-forward down projection in a separate GGUF. It targeted the first token of one mathematically valid correction to the late derivative display. Complete correct training continuations and counterbalanced examples are available for later sequence experiments; this one-point prototype did not train on all of them.

The promotion-only control reproduced all 2,952 Euler decisions, including EOG and the same final display error. The isolated suffix replay matched native residuals, normalized vectors, recorded logits and full-vocabulary log-sum-exp at seven calibration points. Unrecorded individual native logits were not independently compared in that calibration.

Independent payload validation covered all 5,120 output rows and 2,731 supplied states. The stored update's Frobenius norm was 0.70% of the selected control matrix's norm. Actual native target-residual shift was 19.2509878391 against a control norm of 521.4955821872, or about 3.69%, within its 5% cap.

Native replay preserved all 2,730 earlier token decisions and their required margins. At the selected state, the intended token did win: its logit was 23.9195270538, versus 23.7315139771 for the strongest other token. Their margin, **+0.1880130768**, missed the frozen **+0.5** gate. The pairwise proposal had not controlled every competing row.

V8 remains rejected under that gate. A complete free-running Euler answer and fresh evaluations were not run for this candidate; no mathematical improvement or loop-rate result is claimed. The outcome informs a new experiment, with no retroactive change to the failed gate. The candidate SHA-256 and receipt identifiers are in the [public summary](../evidence/experiment-summary.json).

The [bundled streaming-helper receipt](../numerical/terminal-down-stream-v8-verification.json) remains explicitly synthetic: it verifies the numerical helper, including rounding-induced guard leakage. These later curated native observations are separate evidence, with raw checkpoints and capture caches not distributed here.

## V9: native margin passed, complete proof failed

V9 used a rank-one internal update with a multi-competitor exact-RMS proposal and full-vocabulary native cutting-plane checks. It targeted an earlier asserted error at zero-based generated-token index 1,215. The preferred token ID was 426, replacing archived token 560 at that fixed prefix. Token IDs identify this tokenizer and context, not a universal mathematical operation.

The candidate was derived from the F32 D63 promotion-only C of experimental V5/P. Its actual stored matrix change was **0.05199948917%** of the control matrix's Frobenius norm. Its actual native target-residual change was **0.4989041822%** of the control residual norm. Native replay passed the selected full-vocabulary margin at approximately **+0.75** and preserved all **1,215** earlier guarded decisions. All **1,216** checked upstream activation/skip pairs were bit-identical between C and E.

Ordinary Euler generation terminated with EOG after **1,735 tokens**, versus **2,952** for P: 1,217 fewer tokens, about 41.2%. This is a completed-answer length reduction on a training-family case; length alone does not establish a wall-time gain or complete-answer correctness. Manual review of the complete proof was **FAIL**: a displayed derivative used **1/2 where 1/3 was required**. A successful target-token intervention did not establish a correct derivation.

An independent SymPy 1.14.0 check of the observed final body passed the final ODE residual and both initial conditions on $t>0$. The displayed general derivative still failed: claimed minus true derivative was $t(\log t)^3/6$. Thus endpoint correctness is **PASS**, while complete-proof correctness remains **FAIL**.

All seven known ordinary regression completions are now complete and unchanged from the prior frozen P pass: full text, prompt token IDs and EOG completion matched. Their generated-token counts were 679, 110, 122, 191, 1,293, 545 and 479. These are preservation results on known cases.

V9 was **not promoted**; it remains an experimental branch. At the V9 decision, fresh DEV and private held-out material remained unopened. The candidate, native audit, regression and independent mathematical-check receipt hashes are recorded in the [public summary](../evidence/experiment-summary.json). Those private artifact bytes are not bundled; this update publishes no raw reasoning, private question, final body or native source export.

## V10: a complete local repair and a bounded fresh DEV comparison

V10 continued from the experimental V9 checkpoint, changing the same saved F32 terminal down-projection. The proposal worker finished in 38.9 seconds, including input checks, key construction, one multi-competitor exact-RMS solve and native preview; four competitors were active. This measures the proposal phase, not generation speed or the solver alone. Its selected state was zero-based generated-token index **1,607** (zero-based whole-sequence index **1,711**, including 104 prompt tokens), with preferred token 18 replacing archived token 17 at that fixed prefix.

The actual stored incremental change was **0.2440038142%** of the parent matrix's Frobenius norm; the cumulative change relative to the original F32 representation control C8 was **0.2494831489%**. The actual native target-residual shift was **2.4275133587%**. These are norm ratios, not percentages of matrix entries changed. Independent payload validation regenerated every stored F32 bit. Native replay preserved all **1,607** earlier guarded decisions, passed the positive full-vocabulary margin at **+0.7500019073**, and found all **1,608** supplied upstream activation/skip pairs bit-identical.

Ordinary Euler generation completed with EOG after **1,735 tokens**, the same length as V9. All **17 assessed claims in the final proof passed** the mathematical review, and the complete generated token sequence matched the verified preferred continuation. This repairs the displayed derivative defect in this training-family case; it is more evidence than a target-token win, but does not establish unseen mathematical ability.

All seven known ordinary regression completions remained identical to P/V9 in prompt token IDs, complete generated token IDs, full text and EOG completion. Their token counts were 679, 110, 122, 191, 1,293, 545 and 479. A matched original-B comparison independently passed mathematics and format on all seven completed answers. With equal prompts, native parameters, binary and build, B used **5,657 tokens** and V10 used **3,419**, a **39.56160509% cumulative checkpoint-versus-original reduction** across those seven correct completed answers. Those same seven answers already totaled 3,419 tokens in P/V9, so this reduction is inherited and cannot be attributed to V10's incremental internal edit. V10's incremental result is the corrected Euler proof at unchanged V9 Euler length. Six B cases were newly run; the ring comparison used a receipt-bound archived B run. The separate original-B Euler archive stopped at its **3,072-token length cap without a final answer**, versus V10's correct complete proof in 1,735 tokens. That B outcome is **incomplete**, not an incorrect final answer, and is excluded from the seven-completion percentage.

Two fresh DEV inputs were released only after V10's weight fit and core freeze. All four paired V10/B outputs were frozen before either separate oracle was opened. Both models received only the generation inputs, with matched prompts, actual input token IDs, settings, budget and runtime. V10 solved **one of two** correctly; original B solved **zero of two**. The other case remained unresolved for both. V10 had one EOG completion and one 3,072-token length cap; B reached that cap on both. No budget was increased after observing the results.

The report passed the **predeclared fresh relative non-regression** criterion. This is two-case DEV selection evidence, not a held-out capability result. Its verified promotion record now marks V10 **ACCEPTED_TESTED_SCOPE_PROVISIONAL**: it is the next accepted research base A, with original B preserved. Acceptance is limited to the recorded tests and remains distinct from a general mathematical-capability claim. Private held-out material remains closed. A prepared 16-case future TRAIN seed was **not used by V10**; its baseline work is starting from accepted V10. The [public summary](../evidence/experiment-summary.json) records artifact and review hashes without distributing raw prompts, reasoning, final bodies or capture data. These local TRAIN/DEV results establish no wall-time gain, generalized loop removal, global capability or state-of-the-art ranking.

## V11: selected proof repaired, required regression failed

V11 started from accepted V10 and changed the saved F32 terminal down-projection. Stored-weight and prewrite validation passed. Native replay preserved all **483** earlier guarded decisions and passed the positive margin at **+0.75**; all **484** checked upstream feature/skip pairs were bit-identical. The reported stored Frobenius norm ratios were **0.1828% incremental** and **0.3094% cumulative**, with a native positive residual shift of **2.7616%**; these values are rounded norm percentages, not percentages of entries changed.

The selected TRAIN proof passed review after ordinary generation: **806 tokens and EOG**, versus the parent's 803 tokens. It did **not** exactly match the complete teacher token sequence: four later token IDs differed in mathematically valid wording, and the actual complete proof was reviewed as valid. This is a local proof repair with three additional tokens, not a speed improvement or proof that one canonical wording is necessary.

V11 was **rejected** after a different required TRAIN case reached the unchanged **3,072-token length cap without a final answer**. Accepted V10 had completed that same case correctly with **1,399 tokens and EOG**. Thirteen other TRAIN regressions had cleared the preservation criteria before the final batch, including preservation of an already-known proof defect on another case; that defect was not fixed. This does **not** establish that all 15 other TRAIN cases passed. The required new completion regression was sufficient to reject V11.

Remaining Euler, known DEV and previously observed DEV checks were recorded **UNRUN_AFTER_REQUIRED_FAILURE**, rather than counted as passes. V11 was not promoted; accepted V10 remains the research base. The subsequent V12 attempt also started from V10 and is recorded below. The [public summary](../evidence/experiment-summary.json) records the rejection, proof-review, failed-batch and stop receipt hashes without publishing private questions, answers, reasoning or weights.

After preserving receipts and checking dependencies, cleanup removed two obsolete GGUF files and one raw tensor payload. Their logical lengths totaled **23,398,430,528 bytes**. Actual free space rose from **31,363,436,544** to **32,090,370,048 bytes**, an increase of **726,933,504 bytes**. The logical total is not the amount reclaimed. The original, current accepted model and checkpoint anchors/dependencies needed by active work were preserved.

## V12: local repair passed, another proof became inconsistent

V12 again started from accepted V10 and edited the saved F32 terminal down-projection. Canonical payload and physical-checkpoint validation passed. Native replay preserved **247** earlier guarded decisions, passed the positive full-vocabulary margin at **+0.75**, and found all **248** checked upstream feature/skip pairs bit-identical. Stored matrix norm ratios were **0.193% incremental** and **0.315% cumulative**, both rounded. The physical native positive residual shift was **3.7043654595%**; its exact ratio is recorded separately in the [public summary](../evidence/experiment-summary.json).

The selected TRAIN response completed with **494 tokens and EOG**, versus accepted V10's 474. Its complete proof passed review. No complete teacher-token identity or token-saving claim is made.

Two required regressions were moved to the front of the suite with the same original prompts and budgets; all remaining cases stayed required:

| Required regression | Accepted V10 | V12 | Mathematical assessment |
|---|---|---|---|
| First | 745 tokens, EOG | 760 tokens, EOG | Endpoints correct, but a false intermediate scale identity makes the proof inconsistent. |
| Second | 1,399 tokens, EOG | 1,373 tokens, EOG | Complete mathematics passed. |

Independent mathematical review and a separate SymPy check confirmed the first proof's defect. V12 was **rejected and not promoted**. The remaining **13 TRAIN cases**, Euler, known DEV and previously observed DEV were recorded **UNRUN_AFTER_REQUIRED_FAILURE**, not counted as passes. A correct selected proof and one improved regression length did not outweigh the required proof failure; V10 remains accepted.

Cleanup removed the obsolete V12 GGUF and two raw F32 payloads, including the canonical and noncanonical copies. Their logical lengths totaled **12,387,179,424 bytes**. Observed free space increased from **29,493,256,192** to **30,589,423,616 bytes**, or **1,096,167,424 bytes**. This is the observed free-space change, not recovery of the whole logical total. The original, accepted V10, representation anchor and active inputs were retained.

V13 is **preparing** from accepted V10 with a typed TRAIN-only guard set: 247 selected earlier prefixes plus complete accepted-parent responses of 745 and 1,399 tokens, totaling **2,391** rows within the engine's 4,096-row bound. Both complete-response captures qualified. No V13 fit, candidate result or promotion is reported. DEV features do not enter training, and the V11/V12 gates remain unchanged retrospectively. Only aggregate facts and receipt hashes are published; private equations, questions, answers and reasoning remain unbundled.

## Cumulative promotion and storage policy

The improvement loop now uses provisional accepted V10 as the next default research parent. Qualification requires the existing stored/native and complete-answer gates, comparison with both the immediate experimental parent and current accepted reference, and preservation of earlier accepted fixes. A rejected candidate leaves the accepted reference unchanged. Iterative DEV gains do not establish worldwide mastery or an unbiased held-out result.

Retention keeps the original, current accepted checkpoint, one prior accepted rollback, active experimental files and checkpoints that active validators actually read. Older rejected/superseded weights can be pruned after dependency checks while small lineage records and receipts remain. Cleanup uses explicit owned regular-file inventories. On APFS, logical checkpoint size can greatly exceed reclaimed space; actual free space is measured before/after cleanup and before new allocations.

## Keep the evaluation boundary visible

- **Training:** once the observed Euler responses and corrected solutions are used to choose an edit, that family is training material. It cannot subsequently be called a fresh success.
- **DEV:** known derivative, ODE, and regression cases can guide iteration, but repeated use makes their results development evidence.
- **Held-out:** private held-out material remains unopened in this snapshot. Fresh DEV questions are authored only after the relevant training plan is frozen; their oracles stay separate from model inputs and fitting data.

Worldwide school and university mathematics includes substantial unverified coverage: geometry, trigonometry, rigorous analysis, statistics, proofs, applications, languages, notation, and visual inputs. These experiments do not establish worldwide curriculum mastery or a state-of-the-art ranking.

## Reproduce the mathematical checks without loading a model

With SymPy installed, this checks the Euler endpoint, both initial conditions, and reconstructed defective derivative equations from the final exposition. It does not execute model-generated code.

```python
import sympy as s

t = s.symbols("t", positive=True)
L = s.log(t)  # natural logarithm
C1, C2 = s.symbols("C1 C2")
y = t**2 * (1 - 2*L + L**3/6)

residual = t**2*s.diff(y, t, 2) - 3*t*s.diff(y, t) + 4*y - t**2*L
assert s.simplify(residual) == 0
assert y.subs(t, 1) == 1
assert s.diff(y, t).subs(t, 1) == 0

general = C1*t**2 + C2*t**2*L + t**2*L**3/6
true_derivative = s.diff(general, t)
defective_lines = {
    "V5": 2*C1*t + C2*t*(2*L+1) + t*L**2/2 + t*(2*L)**2/6,
    "V7": 2*C1*t + C2*t*(L+1) + t*L**3/3 + t*L**2/6,
}
for label, claimed in defective_lines.items():
    error = s.factor(claimed - true_derivative)
    assert s.simplify(error.subs({t: s.E, C1: 1, C2: -2})) != 0
    print(label, "displayed-derivative error:", error)
```

A correct endpoint can coexist with incorrect working. Record correctness, validity of presented steps, completion, formatting, and token cost separately; then report the complete result, including rejected edits.
