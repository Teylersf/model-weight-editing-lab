# Case study: direct saved-weight edits of Qwen3.8-27B Abliterated

**Research snapshot: 2026-11-04. Project lead: Taylor Kalin.** OpenAI Codex and AI assistants helped develop tooling, check mathematics, and write documentation. The results below distinguish recorded behavior from demonstrated mathematical improvement.

These experiments changed actual saved GGUF weights of **Qwen3.8-27B Abliterated**. The local snapshot was `Huihui-Qwen3.8-27B-abliterated-UD-DW-IQ3_XXS.gguf`, from the [publisher's pinned GGUF repository](https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF/tree/1c69098e9c32db6dc06fc48f1d6cc75ad07da89e). Its verified original SHA-256 was `bfc6892863eceb16f69697e59b038acdc1c709b790c1542e4612dbb0924d3568`. This identifies the specific lab artifact; other conversions and revisions can differ.

The aim was faster, decisive school and university mathematics with correct complete solutions. The base remained immutable while separate candidate files were evaluated. There is no accepted “best mathematics model” result in this snapshot.

## Reading the evidence

**B** denotes the preserved original baseline. In the historical runs, **A** denotes the accepted reference for the run, which became V10 before the Windows work. **P** denotes the experimental V5 parent used through V9. V10 came from the experimental V9 branch while B was the preceding accepted reference. **C** denotes a representation or packing control and **E** denotes an edited candidate. A changed file, a successful numerical fit, a passed saved-prefix check, and an improved complete answer are four different observations.

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

## V13: relative nonregressions passed; promotion declined on token cost

V13 was fitted once from accepted V10 using a typed TRAIN-only guard set: 247 earlier prefixes of the selected case plus complete accepted-parent responses of 745 and 1,399 tokens. These **2,391** guards stayed within the 4,096-row bound; the positive fit state was a separate row. The features came from the identified accepted parent, with explicit case/local-token mapping. DEV and held-out features did not enter fitting, and the rejected V11/V12 gates were not relaxed retrospectively.

A separate physical F32 candidate was written. Independent prewrite validation regenerated the payload F32 bits exactly and recomputed all **2,392** stored-response records. Response floats were compared with relative tolerance **1e-8** and absolute tolerance **1e-12**; types, flags and integers were checked exactly. The independently reconstructed canonical response aggregate hash also matched the producer's in this run. That observed hash match is distinct from the tolerance-based response-float acceptance rule and does not establish bitwise equality with downstream native float vectors.

The stored matrix change was **0.3923178057% incremental** and **0.4649190912% cumulative**; the exact fractions appear in the [public summary](../evidence/experiment-summary.json). Actual native replay then passed all **2,391** guards, with all **2,392** checked upstream feature/skip pairs bit-identical and a positive full-vocabulary margin of **+0.75**. The native positive residual shift was about **3.7044%**, within its 5% cap. Stored-response replay and native replay are distinct checks.

The selected ordinary response completed with **494 tokens and EOG**, versus accepted V10's 474. Independent review of the actual complete final proof, including a SymPy check, passed. This uses **20 additional tokens** on that selected case; it establishes no V13 speed gain.

All **15 required relative mathematical TRAIN nonregressions passed**. Twelve other-case outputs retained all generated token IDs and final-body bytes from accepted V10. This includes an unchanged **803-token EOG** response with an existing invalid proof; that defect was preserved, not fixed. A relative nonregression pass is therefore not a certificate that every displayed claim is correct. The final reviewed pair contained one identical **466-token EOG** response and a changed, mathematically correct **1,729-token EOG** response versus the parent's 984.

Across the original **16-case TRAIN seed**, V13 generated **11,119 tokens** versus accepted V10's **10,113**: **1,006 more tokens**, or approximately **9.9476% more**. The increases were +20 on the selected repair, +89 and +152 on two other correct changed responses, and +745 on the final changed response. This reports token cost, with no latency or throughput claim.

Promotion was **declined by quality selection under the stated fast-output objective**. This was **not a predeclared mathematical-gate failure**, and no predeclared numeric speed threshold is claimed. V10 remains accepted. The TRAIN suite pass does not establish completion of the remaining qualification checks: after selection, the owned Euler core job was interrupted by SIGINT (native return code -2), with **zero completed core groups**. Partial evidence was retained and not counted as passed. The seven known DEV checks and previously observed DEV checks were **UNRUN_AFTER_SELECTION**.

Four parent/candidate/acceptance postchecks matched their own expected hashes and fingerprints. Cleanup batch008 removed **14 obsolete V13 files**: one GGUF, one raw F32 payload and 12 candidate cache arrays. Their logical sizes totaled **12,344,187,808 bytes**. Observed filesystem free space rose from **34,197,118,976** to **35,238,629,376 bytes**, an increase of **1,041,510,400 bytes**; the logical total is not the amount reclaimed. Original B, accepted V10, the C0 representation anchor, accepted-parent control captures and V14 queued inputs were unchanged. Small V13 records and factors were retained, and dependency checks confirmed no active V13 physical dependencies. The [public summary](../evidence/experiment-summary.json) records the final suite, selection and closeout receipt hashes. Guard features remain fitting exposure, and these known TRAIN outcomes establish no broad ability or generalization result. Private questions, equations, teacher/answer bodies and reasoning remain unbundled.

## V14: relative TRAIN checks passed; frozen efficiency gate failed

V14 was fitted once from accepted V10 and written as a separate checkpoint with the edited terminal matrix stored in F32. The rest of the GGUF retains mixed quantized storage. Its method and guard choice were frozen before fitting: the existing 2,391 TRAIN rows plus a qualified complete 984-state accepted-parent response give **3,375 guards and one positive state**. An optional further 601-state response was deferred because of memory uncertainty. The efficiency selection target was frozen before fitting at **no more than 10,113 generated tokens across the same 16 TRAIN cases**, alongside the proof repair and mathematical gates.

Independent prewrite validation recorded a stored matrix change of **0.5010888223% incremental** and **0.5597765742% cumulative**; the exact fractions and receipt hashes appear in the [public summary](../evidence/experiment-summary.json). The physical candidate passed its positive screen at a native margin of **+0.7500019073**, with a positive residual shift of about **3.7044%**, within the 5% cap. A four-case native audit then passed all **3,375** guards; all **3,376** checked upstream feature/skip pairs were bit-identical, and the target margin remained **+0.7500019073**. These are stored/native checks on supplied TRAIN states, not complete-answer or generalization results.

The selected ordinary generation completed with **494 tokens and EOG**, versus accepted V10's 474. Independent review of the **actual complete final proof passed**, including symbolic and complete-prose checks; a separate Mac-side complete-final review also passed. All **15 required relative mathematical TRAIN nonregressions passed**, and all 16 TRAIN generations ended with EOG. One other correct response used **726 tokens versus 720**; the remaining **14 nonselected responses** matched V10 in all generated token IDs and final-body bytes. An existing invalid proof and an inaccurate optional dimensional-units aside were preserved, **not fixed**; relative nonregression does not mean flawless exposition.

The original 16-case TRAIN seed used **10,139 tokens versus accepted V10's 10,113**: **26 more tokens**, or approximately **0.2571% more**. The selected response added 20 and the one other changed response added six. V14 therefore **failed its efficiency ceiling frozen before fitting** and was **not promoted**. This is an efficiency rejection, **not a mathematical rejection**, and supplies no latency or throughput comparison. Core, seven known DEV and previously observed DEV checks were **UNRUN_AFTER_EFFICIENCY_FAILURE**. V10 remains accepted.

Cleanup batch009 removed **18 obsolete V14 files**: one GGUF, one raw F32 payload and 16 candidate cache arrays. Their logical sizes totaled **12,473,162,656 bytes**. Observed filesystem free space rose from **33,951,891,456** to **35,145,293,824 bytes**, an increase of **1,193,402,368 bytes**, rather than the whole logical total. Dependency/runtime-lease checks preceded deletion and the accepted reference remained unchanged. The [public summary](../evidence/experiment-summary.json) binds the final TRAIN suite, disposition, closeout and cleanup receipts; private questions, equations, answer/teacher bodies and reasoning remain unbundled.

The earlier V15 source review proposed a joint proof repair and earlier end-of-generation after the complete proof, using accepted V10, **3,375 TRAIN guards**, two positive states, shared numerical caps and rank at most two. It froze a short complete final proof privately for mathematical supervision. The recorded V15 stage covers the proposal and source review.

## Windows CUDA migration and V22 handoff

The Mac paused after completing and qualifying the V22 TRAIN13 archive capture, before its planned static execution. The frozen transfer manifest lists **3,414 files** totaling **36,069,733,369 bytes**. Windows verified every file against its manifest SHA-256 and length. The transfer included accepted **V10 (E10)**, its C0 reference, and the original rollback. The Mac sender was closed after verification and the Mac lab was kept as a fallback.

Windows ran the accepted checkpoint on an **NVIDIA GeForce RTX 3090 (CUDA0)** using llama.cpp build **11960** (8642541b2), the same build identifier as the Mac. The Windows log recorded **66 of 66 layers offloaded**. The canonical TRAIN13 prompt had the same **100 input token IDs** on both systems. The generations shared the first **65 generated tokens**. Both ended with EOG, at **466 tokens on Metal** and **626 on CUDA**. The Windows final proof passed review. Its measured decode time was **15,833.9793 ms** for that run. The token trajectories diverged, so this run supplies no cross-platform speed or generalization result.

A separate Windows CPU cross-check reused the unchanged archived Mac states. Both archived pairs cleared the necessary support exclusion test. That limited test leaves joint fit feasibility open. Windows fitting requires a fresh CUDA baseline and matching captures. The [public summary](../evidence/experiment-summary.json) records the manifest, build and check hashes.

A fresh Windows control run used the same V10 bytes, prompt bytes, prompt token IDs, and generation settings for all 16 TRAIN cases. The output token sequences matched on **1 of 16** cases. Windows emitted an end token on **15 cases**. The remaining case reached the **3,072-token cap** without producing a final answer. The observed Windows total was **11,961 tokens**, including that incomplete case. Metal emitted **10,113 tokens** across 16 completed answers. These totals describe different trajectories and completion outcomes.

An independent review graded the exact Windows finals. **15 of 15 gradable endpoints** were correct. **12 of 16** passed required mathematical working and modeling, and **11 of 16** passed the stricter check that includes auxiliary claims. The length-capped case was ungradable. This control is for known training cases. Future Windows edits require capture and validation on the actual CUDA trajectories.

A separate archive drive passed independent SHA-256 readback of all **3,414** manifest entries. Forced CUDA replays on accepted V10 matched the ordinary next-token ID at **564 of 564** derivative-proof states and **3,072 of 3,072** states from the length-capped case. The first replay included the observed end token. The second stopped at the observed cap. These are read-only trajectory checks on the unchanged checkpoint.

For the derivative repair, the isolated CUDA suffix matched the captured residual and hidden state bit-for-bit at the selected prefix and an early control. Recorded logit values and winners matched. The full-vocabulary log-sum-exp discrepancy was below `2e-14`. The captures contain a subset of individual native logits, so the per-ID comparison covers that subset.

A separate read-only test checked the ordinary CUDA prefix through its first disagreement with Metal in the capped case. At that one step it emitted the observed Metal token and then resumed free CUDA generation. It again reached **3,072 tokens without a final**. That fixed early-branch hypothesis was closed with the parent checkpoint unchanged.

At the derivative repair state, the ideal dequantized dot product differed from the measured CUDA suffix by up to **0.060855** across 248,320 logits. Reconstructing the Q8_1 input reduced maximum error to **0.000001887** at that state. The historical ideal-head qualification stayed unresolved. The reconstruction checked a specific input. The CUDA source shows where the vector path quantizes the input operand. [Pinned CUDA vector path](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/src/ggml-cuda/mmvq.cu#L1462-L1468)

A separate rank-one proposal used **2,099** Windows guards and a fixed synthetic CUDA gate. Its ideal margin was approximately **0.7500**. CUDA measured **0.7371** against the required **0.7498**, so the attempt stopped before writing a checkpoint. Reconstructing the Q8_1 input at that trial reproduced the observed margin within **0.000001**.

A distinct proposal accounted for the Q8 operand rounding over the same residual budget. Its synthetic CUDA margin was **2.5893**. We wrote a separate GGUF and independently verified the edited F32 bits and every byte outside the terminal down-projection. Its stored matrix change was **0.5257% versus V10**, and **0.5818% versus C0**. The target residual changed by **4.9634%**. Stored readback qualified the file for native replay. CUDA preserved all **2,099** original guard winners and the exact upstream activation and skip inputs at **2,100** states. The selected token won by **2.5893** logits on the physical checkpoint.

In ordinary generation, case07 reproduced the 654-token control exactly. Case08 corrected the derivative and limit, then printed the complete corrected proof twice. It used **716 tokens** against the frozen limit of **564** and emitted two closing markers. The candidate was rejected for format and efficiency. The remaining 14 TRAIN and downstream regression cases were unrun. V10 remains the accepted base.

A separate case16 experiment assembled a mathematically checked compact teacher on the exact CUDA prefix through a complete sentence about nonattainment. The teacher message has **1,362** completion tokens including its end token. This is whole-message token alignment for a proposed intervention. The ordinary case16 control remained capped at **3,072**.

On unchanged V10, emitting just the corrected derivative token at the same case08 prefix produced a **491-token** answer with one closing marker. The persisted candidate and this continuation agreed through that token and diverged at the next step. The shorter answer contained a false intermediate equality, so it did not qualify as a proof target.

In case16, closing the reasoning at the selected semantic boundary produced a free continuation and natural EOG at **1,331 tokens**. The interval and bound were correct. The answer omitted the full coverage and sharpness arguments required by the proof gate. Both interventions were read-only observations.

The rejected checkpoint was moved off the working SSD and verified on the archive drive. The saved comparison and audit receipts remain available.

The [local trace viewer](../prototypes/trace-viewer/README.md) shows the token cap and can display either saved tensor comparison, including C0 versus V10 and V10 versus the Windows candidate. The heatmap summarizes the saved parameter difference by region.

## Preserving the complete proof and ending once

The next Windows edit used the first correct proof from the rejected candidate as the experimental reference. At its complete proof boundary, the end token trailed the repeated closing marker by **0.4710** logits. A separate rank-one D63 update targeted that boundary using **2,321** fitted guards. The rounded synthetic CUDA preview favored the end token by **2.6522** logits. Readback verified the separate GGUF and byte equality outside D63. The stored matrix difference relative to V10 was **0.5917%**.

Replay of the stored checkpoint preserved all **2,321** guarded token choices. The captured upstream arrays matched exactly across **2,322** states. The end token led by **2.6522** logits at the proof boundary.

In ordinary generation the edited checkpoint reproduced the reviewed derivative proof once and ended naturally at **471 tokens**. The paired case07 control matched all **654 tokens**. The full same-backend TRAIN16 comparison then completed all 16 runs with natural end tokens. Independent review found no new mathematical regressions. Among the 15 cases completed by both models, the candidate used **9,437 tokens** and V10 used **8,889**. Case16 separately finished at **1,498 tokens** with the correct interval and error bound. Its proof still lacked the full justification, while the V10 control reached the runtime ceiling without a final answer. The independent core review then passed all eight candidate answers. Fresh Windows V10 gave the correct Euler formula in 1,401 tokens and omitted the derivation. The edited checkpoint recovered the complete Euler proof at 1,762 tokens and preserved all seven known development successes. The observed DEV2 comparison preserved the fresh Windows control's results. Both models gave complete correct proofs on B. Both reached the 3,072-token runtime ceiling on A without a final, whereas historical Mac V10 solved A. The historical preservation gate blocks promotion at this stage.

A read-only follow-up on case16 substituted the runner-up at the candidate's premature end. Free generation added the correct lower-error comparison and ended at **1,516 tokens**. Interval coverage and the argument for approaching the upper bound still need justification. The candidate-free replay showed the next proposed teacher token far below its native competitor, motivating a separate trace at the later ending.

### Saving the partial interval-proof improvement

We used the observed continuation to fit a rank-one edit directly into the F32 terminal down-projection, D63, of the unpromoted Windows proof-stop checkpoint. The fit used **3,722** supplied guard rows. The continuation token trailed the native winner by **3.0942** logits in the experimental parent and led by **2.4680** in the synthetic CUDA preview. Readback of the separate **11,674,147,744-byte** GGUF verified the D63 payload and byte equality outside that tensor. The stored D63 Frobenius differences were **0.6191%** relative to the immediate experimental parent, **0.8564%** relative to V10 (E10), and **0.8919%** relative to the C0 representation control. Each percentage uses its own reference matrix norm.

We loaded the saved candidate and ran case15 and case16 together under the same Windows CUDA settings and exact prompts as the immediate parent. The runner verified the full checkpoint SHA-256 before and after generation. Both answers reached natural end tokens. The case16 candidate emitted the previously reviewed continuation under ordinary greedy decoding.

| Known TRAIN case | Immediate experimental parent | Saved lower-error candidate | Result |
| --- | --- | --- | --- |
| 15 | 700 tokens | 700 tokens | Identical generated token sequence and visible answer bytes. |
| 16 | 1,498 tokens | 1,516 tokens | The candidate added the correct lower-error comparison. Interval coverage and a constructive argument for approaching the upper bound remain missing. |

The interval proof remains incomplete, so the candidate stays unpromoted and V10 (E10) remains the provisional accepted research base. The public summary records the stored matrix fractions and SHA-256 identifiers for the source and receipts. [Public experiment summary](../evidence/experiment-summary.json)

### Complete interval proof from a saved rank-36 edit

The next fit kept 35 residual columns and added the missed full-vocabulary competitor to the one deficient target. All **36** synthetic CUDA targets then passed the **0.7498-logit** floor, with a minimum observed margin of **1.4223**. An independent writer reconstructed the rounded D63 payload, saved a separate **11,674,147,744-byte** GGUF, and verified the edited tensor and byte equality outside it. D63 changed by **4.68%** of the immediate parent's matrix norm and **4.74%** of the accepted E10 matrix norm.

In ordinary greedy CUDA generation, the saved checkpoint reproduced the complete reviewed interval proof and ended naturally after **1,628 tokens**. The proof uses a continuous increasing diagonal to cover the entire interval, shows that the excluded upper limit can be approached, and compares both exact endpoint errors. Its immediate parent's ordinary answer ended naturally after **1,516 tokens** and supplied the endpoint comparison while omitting the coverage and approach arguments.

The three paired controls reproduced their exact previously captured token streams and ended naturally at **471**, **1,036**, and **700** tokens. The interval problem was a known fitting case. [Public experiment summary](../evidence/experiment-summary.json)

We then ran the candidate through all eight original TRAIN16 prompt pairs on the same CUDA runtime and with the same prompts, context, and generation limit as the archived E10 comparison. All **16** answers ended naturally. Independent review passed **14** complete solutions, including newly complete derivative, probability, and interval cases against E10. The two remaining defects were an inherited false modulus equality and an inherited dimensional claim in an ODE answer. Every previously complete TRAIN16 solution passed again. Six previously complete solutions used more tokens, and their correct working passed under the same rubric.

The saved checkpoint's physical CUDA replay preserved all **3,799** guard winners and passed all **36** target margins, with a minimum of **1.4223** logits. Both upstream activation arrays matched the experimental parent's captured bytes exactly. On the downstream core run, the seven known development solutions remained correct and all eight outputs ended naturally. The Euler answer gave the correct final formula but used a false intermediate derivative. The earlier proof-stop checkpoint had given a complete Euler proof under the same CUDA settings. This historical proof regression blocked promotion and the next observed development stage. E10 remains the accepted base.

### Restoring the Euler proof while preserving the interval proof

A read-only probe corrected the first derivative coefficient, then free generation copied that coefficient into the second term. A second controlled probe changed both decisions. It reproduced the independently verified complete proof and ended naturally. This isolated two target states, including the second decision conditional on the first correction. Euler was used as a known preservation case for this fit. The other development cases remained evaluation inputs.

We fit a rank-two update against **10,841** guarded states, comprising **9,503** matched states from the 14 complete TRAIN solutions and **1,338** other states on the approved Euler trajectory. The rounded update passed full-vocabulary CUDA previews at **1.7092** and **1.4772** logits. Independent file readback verified a separate GGUF with byte equality outside D63. Its D63 change measured **6.41%** of the immediate parent's matrix norm and **7.98%** of E10's.

In the saved checkpoint's matched ordinary CUDA run, the interval proof reproduced its exact reviewed answer and ended naturally at **1,628** tokens. The Euler proof reproduced the corrected reviewed answer and ended naturally at **1,340** tokens. Independent review rehashed the saved checkpoint and verified both prompt, token, answer and end-marker streams. This two-case run confirms that both proofs can coexist on the saved weights. [Public experiment summary](../evidence/experiment-summary.json)

All 16 original TRAIN generations then reproduced the rank-36 prompt and completion streams exactly, including their natural end tokens. Independent review confirmed **14 complete solutions**, with the inherited modulus equality and dimensional claim still present in cases 6 and 10. The candidate preserved every previously complete solution against both comparison checkpoints.

Physical replay on the saved checkpoint matched all **10,843** expected token winners across two TRAIN shards and the Euler preservation shard. Both edited Euler positions passed at **1.7092** and **1.4772** logits. The upstream activation and residual-input arrays matched the parent byte for byte in each shard.

The matched downstream core run independently passed all **eight** complete solutions with natural termination. Euler reproduced the corrected proof byte for byte, and all seven other known development cases preserved their complete solutions. The linear-system generation still deliberated about formatting after solving the math, but ended naturally at **1,237** tokens versus **1,504** on rank-36.

The rank-two checkpoint then solved both observed development cases at both matched generation budgets. Independent review checked the complete visible mathematics and confirmed that each candidate answer ended naturally and was identical across budgets.

| Generation budget | Case | E10 | Rank-two |
| --- | --- | --- | --- |
| 3,072 | A | Limit reached without a visible answer | Complete at 1,419 tokens |
| 3,072 | B | Complete at 821 tokens | Complete at 1,080 tokens |
| 6,144 | A | Complete at 5,473 tokens | Complete at 1,419 tokens |
| 6,144 | B | Complete at 821 tokens | Complete at 1,080 tokens |

The rank-two checkpoint used **4,054 fewer tokens** on A and **259 more** on B where both models completed. The original historical comparison and its outcome remain archived under their original settings. This evaluation used two previously observed cases. The separate private holdout remained unopened. [Public experiment summary](../evidence/experiment-summary.json)

The public verifier has been run against the exact local checkpoint and proof streams. The recipe explains how to rerun the pair with the archived inputs and verify the resulting bytes against the reviewed proofs. [Exact reproduction recipe](../prototypes/windows-cuda-ordinary-runner/README.md#verify-the-reviewed-rank-two-proof-pair)

## Extended Windows check on the observed development pair

We reran the two previously observed development cases on V10 (E10) and the Windows proof-stop checkpoint with a matched **8,192-token context** and **6,144-token generation limit**. All four runs ended naturally and passed independent review of the complete visible mathematics.

| Observed case | V10 (E10) | Windows proof-stop checkpoint |
| --- | --- | --- |
| A | 5,473 tokens, 128.789 seconds of decoding | 3,840 tokens, 98.551 seconds of decoding |
| B | 821 tokens, 20.779 seconds of decoding | 798 tokens, 20.949 seconds of decoding |

Each model's A run reproduced its own first **3,072** generated token IDs exactly, then continued to a valid answer. The proof-stop checkpoint used **1,633 fewer tokens (29.8%)** on A in this matched run. Both A traces revisited the same derivation before the final answer. No identical 32-token window repeated within any of the four extended streams. Each B run reproduced its own entire earlier generation and final answer byte for byte. The original 4,096-context, 3,072-generation comparison still records two length-censored A runs and its original promotion decision. The extended comparison covers two observed cases and carries no promotion decision.

## Cumulative promotion and storage policy

The Windows loop now uses the provisional rank-two checkpoint as its next default research parent. The Windows acceptance receipt binds the stored-weight, native replay, complete-answer, and matched regression checks, and the local pointer records E10 as the verified rollback. The original vendor checkpoint and C0 representation reference were independently rehashed before promotion. This decision covers the tested Windows cases. Worldwide curriculum coverage and fresh held-out performance remain open. [Acceptance hashes and gate results](../evidence/experiment-summary.json)

Subsequent edits compare against both the immediate experimental parent and the current accepted reference, and must preserve earlier accepted fixes. A rejected candidate leaves the accepted reference in place.

For future Windows evaluations, a correct, complete solution may take longer than the matched control. Record token counts, decode time, and repeated work separately. Compare speed among equally correct, complete solutions. Keep the native generation ceiling as an execution limit and record a ceiling hit as a censored run. Use the former per-case and aggregate token thresholds, including the case16 readiness target, as performance references. The historical dispositions above document the rules used at the time.

Measure the actual stored matrix change relative to each relevant reference. Subsequent Windows edits use that measurement to compare candidates, with promotion based on stored-byte verification, native replay, complete solutions, natural completion, and matched regressions. The 1% matrix gate applies to the historical runs that declared it. New trials can explore larger changes when the observed proof and margin evidence justifies doing so.

A CPU diagnostic reapplied the earlier two-target interval screen without the cumulative matrix cutoff. It tested local residual allowances of **5%, 7.5%, 10%, and 15%**. The stricter target was excluded by the conservative pairwise **+0.75** margin screen below about **9.944%**. Both targets cleared their separate necessary screens at 10% and 15%, conditional on the quantized operand error model. At 10%, the uniform upper estimate for the cumulative D63 Frobenius difference relative to E10 was **1.93%** of the E10 matrix norm. The estimate covers independent residual allowances and leaves joint fit feasibility and native behavior unresolved. The sweep used captured inputs and produced no fitted update or saved weight change.

A separate Windows trial fit the **36** observed token disagreements along an independently reviewed complete interval proof. The CPU projection used **3,799** already-matched states, including the full trajectories of three prior solutions. The rounded F32 proposal measured **4.67%** relative to its immediate parent and **4.72%** relative to E10. In the full-vocabulary CUDA preview of the proposed residuals, all 36 intended tokens won. Thirty-five cleared the **0.7498-logit** minimum. The remaining target led by **0.2698** against a token outside its original four-competitor fit. The proposal was held before checkpoint materialization. The separate stored-checkpoint and ordinary-generation tests remain necessary.

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

## Sixth pilot: finish after the calculation is settled

This pilot edits one decision in the accepted rank-two checkpoint. On an authored cylinder problem, the parent found the exact volume \(39.366\pi\) and had enough precision to round it correctly, then started another manual calculation. The edit trains the token that ends the reasoning phase at that decision. It leaves the model free to write its own visible solution.

We fit a rank-one update to the saved layer 63 down projection against 10,876 projected guard states. At the fixed prefix, the desired token went from 10.616 logits behind the winner to 3.150 ahead in the full-vocabulary CUDA preview. The stored D63 difference is 2.994% of the parent's matrix norm. Independent readback verified every byte outside that matrix.

In ordinary generation, the candidate reproduced the first 86 tokens, chose to finish reasoning at the intended decision, and gave the cylinder formula and correct answer, **123.7 cubic centimeters**. It ended naturally in **204 tokens**, compared with **486** for the parent. Decode time was **4.64 seconds** versus **10.55 seconds** on this matched run.

Both models solved all six authored development problems and ended naturally. Two control outputs matched token for token; the other three remained correct and used 9–37 more tokens each. The combined count went from **2,978 to 2,756**. These are development results. The parent already knew the math, and the experiment has not established a general reduction in looping or a gain in accuracy. The accepted checkpoint remains in place. [Saved-weight and matched generation evidence](../evidence/direct-closure-pilot-006.json)

The interval-bound and Euler differential-equation proofs reproduced the accepted token streams and final text exactly. Codex also verified the interval endpoints and sharpness argument and checked the differential equation and both initial values symbolically.

A separate blind comparison used six new authored problems: four requiring exact answers and two requiring rounding. Both checkpoints produced **6/6 complete correct answers** in the requested format, with natural endings on all six. The candidate used **5,253 total tokens versus 5,740** for the parent (8.5% fewer). It used fewer tokens on two problems, the same on one, and more on three. Median tokens rose from **606.5 to 635**. Median measured decode time went from **15.77 to 14.17 seconds** in this run. The small set provides a check on accuracy and format; it does not establish a consistent speedup. [Blind grading and paired aggregates](../evidence/direct-closure-pilot-006.json)

On the same 370 MMLU items, the candidate matched the parent's **226/370**: 162/270 in high school and 64/100 in college. One high-school answer became correct and one became incorrect; all 100 college choices matched. The unchanged score therefore still includes an individual regression. The edit remains experimental. [Paired MMLU and disposition](../evidence/direct-closure-pilot-006.json)

## Seventh pilot with a smaller update

Pilot 007 reused the accepted parent and the pinned development capture from Pilot 006. A native search tried five fractions of the fitted update. The smallest tested fraction to clear a margin of one logit was 0.85. After storage rounding, the target still led by 1.060 logits. The saved change measured 2.545% of the parent's layer 63 matrix norm, and readback verified exact bytes outside that matrix.

The cylinder answer again finished naturally in **204 tokens versus 486**, with the same correct answer and working. Its measured decode time fell from **10.55 to 5.04 seconds**. Both checkpoints got all six development answers right. Combined token count fell from 2,978 to 2,756, while measured decode time for the six cases rose from 64.78 to 68.16 seconds. [Pilot 007 evidence](../evidence/direct-closure-pilot-007.json)

The 370-question MMLU comparison returned **226/370** for each model. One high-school answer became correct and one previously correct answer became incorrect. All 100 college choices matched. The pilot failed the requirement to preserve every correct answer from the accepted checkpoint. [Paired results](../evidence/direct-closure-pilot-007.json)

Pilots 006 and 007 made identical choices on all 370 MMLU questions, including both changed high-school answers.

## Eighth pilot at a later stopping point

Pilot 008 guarded the original continuation at token 86 and targeted the next unnecessary recalculation at token 164, after the parent obtained 123.671. At that state the finish token was 5.492 logits behind the winner. The rounded preview put it 3.143 logits ahead. The saved update measured 1.873% of the parent matrix norm, and both exterior byte spans matched exactly.

The edited cylinder run matched the first 164 tokens of the parent and then ended reasoning. It gave the correct worked answer in **282 tokens versus 486**, with measured decode time of **6.63 seconds versus 10.55**. All six development answers had correct mathematics and ended naturally. The new probability answer had a visible formatting defect in its first LaTeX table. Across the six cases, tokens fell from 2,978 to 2,934 and measured decode time rose from 64.78 to 68.51 seconds. [Pilot 008 evidence](../evidence/direct-closure-pilot-008.json)

On the matched MMLU questions, Pilot 008 scored **225/370 versus 226/370** for the parent. One previously correct high-school answer was lost. All college choices matched the parent. [Paired results](../evidence/direct-closure-pilot-008.json)

## Ninth pilot with probability format guards

Pilot 009 kept the later cylinder target and added 18 guard states from the accepted probability answer. These covered the first changed decision and the original table structure. The fit used development trajectories. The stored change measured 1.880% of the parent matrix norm, and independent readback verified exact bytes outside the matrix.

The probability answer reproduced the accepted 634-token sequence with both original five-column tables. The cylinder answer again ended reasoning at token 164 and finished in **282 tokens versus 486**, taking **6.56 seconds versus 10.55** to decode. All six development answers were correct and ended naturally. Combined tokens fell from 2,978 to 2,811. Measured decode time was 65.13 seconds versus 64.78 for the parent. [Pilot 009 evidence](../evidence/direct-closure-pilot-009.json)

Pilot 009 made the same choices as Pilot 008 on all 370 MMLU questions. It scored **225/370 versus 226/370** for the parent, with one previously correct high-school answer lost and all college choices preserved. [Paired results](../evidence/direct-closure-pilot-009.json)

## Tenth pilot with a smaller update at the later decision

Pilot 010 reused the pinned Pilot 009 capture and searched five update scales using the development logits. Scale 0.75 led by 0.963 logits and scale 0.85 led by 1.878. The latter cleared the one-logit screen and the rounded preview. The saved change measured 1.598% of the parent matrix norm. Independent readback verified exact bytes outside the matrix.

All six development outputs matched Pilot 009 token for token. The cylinder still finished in **282 versus 486 tokens**, with measured decode time of **6.51 versus 10.55 seconds**. The probability tables retained the accepted format. All answers were correct and ended naturally. Across six cases, total tokens fell from 2,978 to 2,811, with measured decode time of 64.87 seconds versus 64.78 for the parent. [Pilot 010 evidence](../evidence/direct-closure-pilot-010.json)

Pilot 010 scored **225/370 versus 226/370**, with the same 370 choices as Pilot 009. Pilots 006 through 010 all lost the same previously correct high-school item. An independent audit found that the accepted model's correct option had led by only 0.00217 logits on that item. The loss still counts in the paired comparison. [Paired results](../evidence/direct-closure-pilot-010.json)

## Eleventh pilot after restating the exact expression

Pilot 011 targeted token 178 after the parent restated \(39.366\pi\). The rounded preview put the finish token 3.242 logits ahead. The saved change measured 2.934% of the parent matrix norm. Independent readback verified exact bytes outside the edited matrix.

The ordinary cylinder trajectory diverged at token 76 and reached its finish token at 237. It gave the correct worked answer in **371 tokens versus 486**, below the 25% reduction required to advance. The population response also closed reasoning at token 36 and gave **762 instead of 798**. The probability response and its table matched the accepted output exactly. Five of six development answers were correct. The candidate stopped at the development gate. [Pilot 011 evidence](../evidence/direct-closure-pilot-011.json)

## Twelfth pilot with a measured stopping point and finer dose

A single replay of the unedited development trajectory measured the finish token at seven potential stopping points. Token 164 had the smallest deficit, 5.492 logits. The fit returned to that point and protected the development decisions that changed prematurely in Pilot 011. A finer search selected a scale of 0.755 and the rounded preview put the target 1.016 logits ahead. The saved change measured 1.423% of the parent matrix norm, with byte equality outside the matrix.

All six development responses ended naturally and were correct. The cylinder matched the parent's first 164 tokens and finished in **282 versus 486 tokens**, taking **6.50 versus 10.55 seconds** to decode. Four answers matched the parent token for token, including the probability tables and the population estimate. [Pilot 012 evidence and scan](../evidence/direct-closure-pilot-012.json)

Pilot 012 scored **225/370 versus 226/370** on the matched MMLU comparison. The one previously correct answer it lost was the same item Pilot 010 lost. The finer dose retained the development gains while the matched accuracy gate still failed. [Paired results](../evidence/direct-closure-pilot-012.json)

## Thirteenth pilot with answer-choice constraints

The last-layer residual update can be constrained using only the output rows for the four literal answer letters. The solver projects the update into the null space of their three independent RMS-gain-weighted differences. In the decoded real-arithmetic model, a fixed prefix then keeps its choice order because RMS normalization multiplies the differences by a common positive factor. The native CUDA kernel and rounded stored matrix require their own checks.

The constrained fit reused the pinned development capture and selected a scale of 0.755. The native preview gave the finish token a **1.007-logit** lead and preserved the four-letter order at that one fixed development state. The maximum stored pairwise contrast operator norm was \(7.88\times10^{-8}\). Readback verified exact bytes outside the edited matrix.

The cylinder again ended reasoning at index 164 and finished naturally in **282 versus 486 tokens**, with the correct worked answer. Measured decode time was **6.82 versus 10.55 seconds**. All six development responses were correct and matched Pilot 012 token for token. The six-case aggregate decode time was 68.61 seconds versus 64.78 for the parent. [Pilot 013 evidence](../evidence/direct-closure-pilot-013.json)

Pilot 013 made the same choices as Pilot 012 on all 370 MMLU questions and scored **225/370 versus 226/370** for the parent. The algebraic choice constraint and the one-state native check did not prevent the matched regression. In the pinned CUDA path the Q4_K head uses a Q8_1 activation quantizer, which can change differences between native logits beyond the decoded real-arithmetic model. [Paired results](../evidence/direct-closure-pilot-013.json) · [Pinned CUDA quantizer](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/src/ggml-cuda/quantize.cu#L74-L90)

## Fourteenth pilot with authored choice prompt guards

Pilot 014 kept the answer-choice constraint and added 16 original four-choice prompts across school and college mathematics. One pass captured the accepted model's final prompt activations and next-token winners. A guarded second pass reproduced the activations and winners exactly. Each prompt contributed one guard state and supplied no fit target.

The rounded target margin stayed at **1.007 logits**, and the saved edit measured **1.428%** of the parent matrix norm. Readback verified exact bytes outside the matrix. All six development answers were correct and ended naturally. The cylinder closed reasoning at index 164 and finished in **282 versus 486 tokens**, taking **6.17 versus 10.55 seconds** to decode. The probability tables and population estimate matched the parent token for token. [Pilot 014 evidence](../evidence/direct-closure-pilot-014.json)

The saved candidate replay reproduced all 16 authored guards' full-vocabulary winners and all four selected choice logits exactly. Its matched MMLU result was **225/370 versus 226/370** for the parent, with the same choices as Pilot 013. Exact preservation on those authored states did not prevent the recurring benchmark loss. [Saved-guard replay and paired results](../evidence/direct-closure-pilot-014.json)

A fresh run of the unchanged accepted checkpoint reproduced **226/370** and every one of the four native logits on all 370 prompts. The correct answer's 0.00217056-logit lead on the recurring loss reproduced exactly. That confirms the regression in the matched edited runs. [Accepted checkpoint recheck](../evidence/direct-closure-pilot-014.json)

## Fifteenth pilot with close-distractor guards

Pilot 015 added 16 independently authored four-choice stress prompts across school and college math. Discovery and guarded capture reproduced their activations and logits exactly. The smallest gap between the two leading choice logits was **0.04391**, and none was below **0.02**. The stress pack therefore gave no direct coverage of the recurring loss's much smaller 0.00217-logit lead. [Pilot 015 evidence](../evidence/direct-closure-pilot-015.json)

The saved layer 63 edit retained six correct development answers with natural stops. The cylinder finished in **282 versus 486 tokens** and took **6.76 versus 10.55 seconds** to decode. Combined development tokens fell from 2,978 to 2,811, while combined measured decode time rose from 64.78 to 67.49 seconds. [Generation results](../evidence/direct-closure-pilot-015.json)

All 370 choices matched Pilot 014. The checkpoint again scored **225/370 versus 226/370** for the accepted parent and lost the same previously correct high-school answer. The run stopped before regenerating the two prior proofs or opening the fresh evaluation. This fit inherited archived proof activations in its guard projection. The next fit excluded those activations so that the proofs could serve as separate generation checks. [Matched benchmark results and input provenance](../evidence/direct-closure-pilot-015.json)

## Sixteenth pilot with one output row

The next edit changed the row of `output.weight` for the existing reasoning-finish token, ID 248069. At a fixed prefix this is a direct way to change that token's score. The hidden-state weights, token embeddings, and output rows for the four benchmark choice letters remain byte-identical. During ordinary generation an earlier finish can still change the rest of the sequence, so complete-answer checks remain necessary.

The fit kept the Q4_K block scales and minima fixed and changed only the packed 4-bit codes. It used the native parent output norm and modeled the CUDA Q8_1 activation quantization to estimate the logit change from each code step. The fit protected native winners on 3,191 development states, covering all positions in six accepted answers apart from the intended intervention, a forced-prefix continuation from the earlier finish, and additional development and authored guards. Historical proof activations, the benchmark questions, and the fresh evaluation were excluded. [Pinned CUDA quantizer](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/src/ggml-cuda/quantize.cu#L74-L90) · [Pinned Q4_K row dot product](https://github.com/ggml-org/llama.cpp/blob/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/src/ggml-cuda/vecdotq.cuh#L909-L917)

The saved file changed **315 bytes in one 2,880-byte row**. At the target prefix, the reloaded native computation reproduced both hidden-state captures and all **248,319** other logits bit for bit. The finish token led by **0.8211 logits**. Independent review found all six development answers correct and complete with natural stops. The cylinder closed at index 164 and gave **123.7 cm³** in **282 versus 486 tokens**. Its measured decode time was **6.46 versus 10.55 seconds**. The five other answers matched exactly. Combined decode time was 63.93 seconds versus 64.78 seconds for the parent.

On matched MMLU, Pilot 016 preserved all 370 choices and every one of the **1,480 binary32 choice logits**. Both checkpoints scored **226/370**, with 162/270 in high-school math and 64/100 in college math. The interval proof reproduced exactly. The Euler run differed at token 620, where the edited finish token won. It ended naturally in 1,380 tokens versus 1,340 for the parent. Independent substitution showed that its new particular solution produced six times the required forcing term, so the answer was incorrect. The fresh evaluation stayed sealed. [Pilot 016 evidence](../evidence/direct-closure-pilot-016.json)

The published sparse XOR patch can reproduce this candidate given the exact accepted parent. Run `python examples/replay_output_row_edit.py --parent PATH_TO_PARENT.gguf` to verify both whole-file SHA-256 digests without writing a checkpoint. On a filesystem that supports hard links, add `--output NEW_CANDIDATE.gguf` to save a verified copy. The published data contains only the row deltas and metadata needed for this edit. [Patch data](../evidence/direct-closure-pilot-016-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Seventeenth pilot with tighter localization

Pilot 017 retained the one-row edit and changed how the packed weights were fitted. A ridge solution localized the intended score change, then integer rounding and coordinate exchanges enforced the target and the original 3,191 winner constraints. Across those states, the 95th-percentile absolute change in the finish token's logit fell from **2.416 to 0.271**, and the maximum fell from **5.376 to 1.227**. The edit changed 23.61% of the original row norm, up from 17.01% in Pilot 016. The lower off-target score change came from where the weights changed.

The accepted model hit the 2,048-token limit on all eight additional authored proof-development cases. Five produced no visible answer. Two supplied correct partial work and one supplied incorrect partial work. None met the natural-stop and correctness criteria for fit input. The original 3,191 development constraints remained the complete fit set. [Fit and exclusion receipts](../evidence/direct-closure-pilot-017.json)

The checkpoint changed **1,797 bytes in the same 2,880-byte row**. At the fixed cylinder prefix, both hidden-state captures and all 248,319 other logits matched the accepted parent. The finish token led by **0.82006 logits**. Independent review found all six development answers complete and correct. The cylinder finished in **282 versus 486 tokens** and decoded in **6.46 versus 10.55 seconds**. The other five answers reproduced exactly.

Pilot 017 reproduced the Euler proof exactly. The interval response matched up to the accepted finish decision at index 1218, then continued thinking. It reached the 3,072-token limit without a visible proof, versus a natural ending at 1,628 tokens for the parent. The exact proof gate stopped the pilot before matched MMLU or the fresh evaluation. The accepted checkpoint remained in use. [Proof receipts](../evidence/direct-closure-pilot-017.json)

Run `python examples/replay_output_row_edit.py --pilot 17 --parent PATH_TO_PARENT.gguf` to verify the resulting whole-checkpoint digest from the exact accepted parent. [Patch data](../evidence/direct-closure-pilot-017-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Eighteenth pilot with proof-ending controls

Pilot 018 added 200 fixed-prefix states from eight independently authored development proofs. The native runner replayed the teacher tokens and measured its own winner at each state. The fit constrained those native decisions and the change in the finish score around each teacher finish. It also protected 11 natural finish positions from the original development captures. The two prior proofs, MMLU questions, fresh evaluation, and eight capped model traces remained outside fitting. [Fit and input provenance](../evidence/direct-closure-pilot-018.json)

The fit kept all 3,391 predicted winner constraints and reduced the maximum finish-logit change at the 11 natural development finishes from **0.257 to 0.042**. The original development set's 95th-percentile change rose from **0.271 to 0.484**. The largest change across the combined states was **0.763 logits**. The saved checkpoint changed 1,880 bytes inside the one output row.

At the cylinder prefix, both hidden states and all 248,319 other logits were bit-identical. The finish token led by 0.82078 logits. Independent review again found all six ordinary answers correct and complete. Five matched exactly, and the cylinder gave 123.7 cm³ in **282 versus 486 tokens**, taking **6.43 versus 10.55 seconds** to decode.

Euler replayed exactly. The interval run changed its decision at index 1218 and generated the same capped stream as Pilot 017. It reached 3,072 tokens without a visible proof. Lower score changes at the captured finish positions did not preserve this separate interval case. The pilot stopped before the matched benchmark and fresh evaluation. [Proof receipts](../evidence/direct-closure-pilot-018.json)

Run `python examples/replay_output_row_edit.py --pilot 18 --parent PATH_TO_PARENT.gguf` to verify the checkpoint digest. [Patch data](../evidence/direct-closure-pilot-018-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Nineteenth pilot with a smaller target margin

Pilot 019 reduced the target margin floor from 0.82 to 0.30 logits and required a small positive finish-score change at all 11 observed natural closing states. The packed fit retained the 3,391 signed winner constraints and the teacher closure bounds. Four searches using a two-code limit missed the constraints. The qualifying fit used a three-code change at four of 2,499 changed nibbles. On the same 3,391 states, the 95th-percentile absolute change fell from **0.485 to 0.424 logits**, and the maximum fell from **0.763 to 0.653**. [Fit evidence](../evidence/direct-closure-pilot-019.json)

Saved-file readback verified 1,876 changed bytes inside the one output row. The native preview preserved both hidden states and all other token logits, with a **0.306-logit** lead at the cylinder finish. Independent review found six correct, complete, naturally ended development answers. The cylinder still gave **123.7 cm³** in **282 versus 486 tokens** and took **6.45 versus 10.55 seconds** to decode. The other five answers matched exactly.

Euler again replayed exactly. The interval output was byte-identical to the failed Pilot 018 stream. It missed the accepted finish decision at index 1218 and hit the 3,072-token cap without a visible proof. The pilot stopped before matched MMLU and fresh evaluation. [Proof receipts](../evidence/direct-closure-pilot-019.json)

Run `python examples/replay_output_row_edit.py --pilot 19 --parent PATH_TO_PARENT.gguf` to verify the checkpoint digest. [Patch data](../evidence/direct-closure-pilot-019-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Twentieth pilot with late proof controls

Four newly authored proofs covered graph optimization, number theory, linear algebra, and probability. Their teacher reasoning ranged from 1,118 to 1,215 tokens. The accepted runtime replayed them and measured 172 states, including 12 positions on either side of each intended finish. The finish token was the native winner at all four authored closing positions. These were forced development contexts. The prior proofs and the fresh evaluation remained outside fitting. [Input and capture evidence](../evidence/direct-closure-pilot-020.json)

The fit retained 3,563 signed winner constraints and small positive changes at the 11 original and four long native closing positions. The long-state 95th-percentile absolute score change fell from **0.659 to 0.206 logits** compared with Pilot 019. On the prior development states it fell from **0.424 to 0.391**, while the maximum rose from 0.653 to 0.669. The decoded packed row passed the declared limits.

Readback verified 1,777 changed bytes in the same output row. The native preview preserved both hidden captures and all 248,319 other logits. Independent review found six correct, complete development solutions with natural stops. Five matched exactly. The cylinder gave **123.7 cm³** in **282 versus 486 tokens**, decoding in **6.38 versus 10.55 seconds**.

Euler replayed exactly. The interval proof diverged at index 1218 and produced the same capped stream as Pilot 019, with no visible proof. The exact proof gate stopped the experiment before MMLU and fresh evaluation. [Proof receipts](../evidence/direct-closure-pilot-020.json)

Run `python examples/replay_output_row_edit.py --pilot 20 --parent PATH_TO_PARENT.gguf` to verify the checkpoint digest. [Patch data](../evidence/direct-closure-pilot-020-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Twenty-first pilot with a four-row output edit

Pilot 021 increased the closing score and reduced three competing token scores using the same 3,563 development guard states. The saved GGUF changed 3,204 bytes across four `output.weight` rows. At the cylinder prefix, the captured hidden states and 248,316 other logits matched exactly, and the closing token led by **0.368 logits**. The correct cylinder answer took **282 versus 486 tokens** and **6.50 versus 10.55 seconds** to decode. The five other correct development outputs matched exactly. [Fit, readback, and generation evidence](../evidence/direct-closure-pilot-021.json)

The interval proof replayed exactly. Euler ended naturally and gave the requested exact solution. Independent symbolic substitution verified the equation and both initial conditions. Its visible answer was shorter, and its token stream diverged at index 53. The parent chose token `6558` (` Let`), whose output row was edited. The pilot chose token `1061` (` This`), whose row was unchanged. With identical prefixes and only output rows edited, that change identifies the local source of this divergence. The exact proof gate stopped the experiment before matched MMLU and fresh evaluation. [Proof receipts](../evidence/direct-closure-pilot-021.json)

Run `python examples/replay_output_row_edit.py --pilot 21 --parent PATH_TO_PARENT.gguf` to verify the checkpoint digest. [Patch data](../evidence/direct-closure-pilot-021-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Twenty-third pilot with a rank-one feed-forward edit

Two intervening packed output-row variants cleared development fitting. An evaluation-only CPU replay predicted both would miss the interval proof's closing decision, so those rows stayed as compact proposals. [CPU screening method and timing](weight-editing-research.md#where-to-shorten-the-loop)

Pilot 023 changed `blk.63.ffn_down.weight` while leaving the output head byte-identical. One factor made the update respond at the cylinder decision while nearly canceling its response across 3,563 development states. The other factor moved the residual toward choosing the finish token. The fit used only development data. After rounding to the stored F32 representation, the update's Frobenius norm was 0.631% of that tensor's norm. [Fit and readback evidence](../evidence/direct-closure-pilot-023.json)

CUDA replay on the saved GGUF reproduced the **+0.14522-logit** finish margin and kept all 31 control winners. Thirty control logit vectors matched the accepted model bit for bit. The remaining control's largest absolute change among the four benchmark choice logits was **0.000275**. The earlier synthetic replay used an already computed residual. Recomputing the edited matrix on original inputs changed the residual and normalized-state bytes, which is why the saved-file replay is a separate check. [Native preview and physical replay](../evidence/direct-closure-pilot-023.json)

Independent review found all six ordinary development answers correct and complete. The cylinder finished naturally in **282 versus 486 tokens**, decoding in **6.52 versus 10.55 seconds**. The other five outputs matched exactly. Across the six development cases, decode time was 63.70 seconds versus 64.78 for the parent. [Ordinary generation and independent grade](../evidence/direct-closure-pilot-023.json)

The two accepted proofs both diverged during ordinary generation. The interval trace changed at index 219 and reached the 3,072-token cap without a visible answer. Euler changed at index 53 and ended naturally in 1,441 tokens versus 1,340. Its exact expression satisfied the equation and both initial conditions under independent symbolic substitution. The exact proof gate stopped the experiment before the matched benchmark and fresh evaluation. [Proof receipts](../evidence/direct-closure-pilot-023.json)

Run `python examples/replay_d63_rank_one_edit.py --parent PATH_TO_PARENT.gguf` to independently rebuild the edited tensor in memory and verify the whole candidate SHA-256 without writing a GGUF. [Exact factors and extent](../evidence/direct-closure-pilot-023-d63-patch.json) · [Replay code](../examples/replay_d63_rank_one_edit.py)

## Twenty-fourth pilot with a blended finish direction

The fit blended the normalized closing-row directions from Pilots 021 and 020, projected the blend against 3,563 authorized development states, then repaired the packed Q4_K codes. Two distinct rows passed the development fit and were frozen before proof screening. The archived CPU screen predicted that the blended row would preserve both accepted proof sequences. The other row was predicted to miss the interval closing decision. [Fit and selection evidence](../evidence/direct-closure-pilot-024.json)

The saved blended edit changed **1,996 bytes** in the finish-token row. CUDA gave the finish token a **0.06199-logit** lead at the cylinder decision while preserving both hidden-state captures and all 248,319 other logits. The correct cylinder answer ended naturally in **282 versus 486 tokens** and decoded in **6.46 versus 10.55 seconds**. The five other development outputs matched exactly. [Saved native and development results](../evidence/direct-closure-pilot-024.json)

Ordinary generation reproduced both accepted proofs, their visible answers, and their natural end tokens exactly. The interval proof took **1,628 tokens**, and Euler took **1,340**. This confirmed the archived screen's prediction for the saved checkpoint. [Exact proof receipt](../evidence/direct-closure-pilot-024.json)

The matched public MMLU run preserved every choice and all **1,480 binary32 answer logits** across **370** questions. Both models scored **226/370**, with 162/270 in high-school mathematics and 64/100 in college mathematics. The candidate preserved all 226 previously correct answers. [Matched benchmark receipts](../evidence/direct-closure-pilot-024.json)

On six independently graded fresh problems, both models scored **6/6 complete and correct** with natural endings and zero paired losses. The grader saw only randomly labeled visible answers and the rubric. Five responses matched exactly. The sixth stayed correct and used six more tokens. Median response length was **975.5 tokens** for both models, and measured median decode time was **21.81 seconds** for the candidate versus **21.49** for the parent. The speedup was concentrated in the cylinder case. [Blind grading and matched native receipts](../evidence/direct-closure-pilot-024.json)

Run `python examples/replay_output_row_edit.py --pilot 24 --parent PATH_TO_PARENT.gguf` to verify the whole checkpoint digest from the exact accepted parent. [Patch capsule](../evidence/direct-closure-pilot-024-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Twenty-sixth pilot with option-order repairs

The Pilot 024 diagnostic found that rotating the same answer choices changed the selected mathematical content. The follow-up used 32 independently authored and independently solved development problems. Pilot 024 answered 42 of 128 cyclic orders correctly. It changed correctness across orders on 27 of the 32 items and answered none correctly in all four orders. [Diagnostic and independent solution audit](../evidence/mmlu-accuracy-diagnostic-026.json)

Pilot 026 directly edited two directions in the stored F32 tensor `blk.63.ffn_down.weight`. The fit targeted one missed rotation on each of two authored problems, with 126 other authored rotations and 635 previously authored states as controls. The fitter saw only authored development inputs. The rounded edit's Frobenius norm was 0.306% of that tensor's norm. Byte-for-byte readback verified that the remainder of the GGUF, including the output head and reasoning-finish row, matched Pilot 024. [Fit and readback evidence](../evidence/direct-accuracy-pilot-026.json)

CUDA replay of the saved model preserved all 126 control choices and gave the two targeted answers leads of 1.167 and 1.232 logits. Ordinary inference on the identical 128 development prompts confirmed both changes and zero losses. Pilot 026 scored 44/128 and answered both targeted problems correctly in all four orders. These results use the development prompts from fitting. [Native replay and ordinary development evidence](../evidence/direct-accuracy-pilot-026.json)

The cylinder answer matched Pilot 024 and ended naturally at **282 tokens**, retaining the improvement from 486 tokens in the earlier reference. Both accepted proofs failed the exact replay gate. Each reached the 3,072-token cap without a visible answer, compared with natural endings at 1,628 and 1,340 tokens on Pilot 024. [Proof and cylinder results](../evidence/direct-accuracy-pilot-026.json)

On the matched 370-question MMLU run, Pilot 026 scored **222/370 versus 226/370**. Four previously correct high-school answers became wrong, and no prior miss became correct. College accuracy stayed at 64/100. The independent fresh set stayed sealed after the failed gates. Pilot 026 remains a rejected experiment, and the accepted model pointer stayed in place. [Paired benchmark evidence](../evidence/direct-accuracy-pilot-026.json)

With the exact Pilot 024 GGUF, run `python examples/replay_d63_rank_two_edit.py --parent PATH_TO_PILOT_024.gguf` to reconstruct the edited tensor in memory and verify the full Pilot 026 checkpoint hash. The replay only reads the parent checkpoint. [Patch capsule](../evidence/direct-accuracy-pilot-026-d63-patch.json) · [Replay code](../examples/replay_d63_rank_two_edit.py)

## Twenty-seventh pilot with two packed answer rows

Pilot 027 starts from Pilot 024 and fits the same two authored rotation repairs by changing 58 single-step Q4_K codes across the ` A` and ` B` output rows. The fit used the original 128 authored states and 635 prior authored controls. Readback verified byte equality across the rest of the checkpoint, including the D63 tensor and the reasoning-finish row. The quantization block metadata matched the parent on both edited rows. [Fit and readback evidence](../evidence/direct-accuracy-pilot-027.json)

On the 128 captured states, the in-memory CUDA preview changed logits only for ` A` and ` B`. Both targeted answers led by about 0.10 logits across the full vocabulary, and all 126 guards preserved their restricted and full-vocabulary winners. CUDA replay from the saved GGUF reproduced all 128 complete logit vectors bit for bit. Ordinary inference confirmed a gain from 42/128 to 44/128, both repairs and zero losses on the fitting prompts. [Native and authored results](../evidence/direct-accuracy-pilot-027.json)

On a separate 32-question authored development set, the edit scored **71/128 versus 70/128** across cyclic orders. Two orders improved and one regressed. Both models answered eight items correctly in all four orders. The number of items with the same selected content in all four orders fell from 12 to 11. This exploratory set was held out of the fit. [Transfer diagnostic](../evidence/direct-accuracy-pilot-027.json)

On matched MMLU, Pilot 027 scored **225/370 versus 226/370**. One previously wrong answer became correct and two previously correct answers became wrong. All three correctness changes were on high-school mathematics. Both exact proofs and the correct 282-token cylinder answer replayed. The cylinder took 6.97 seconds to decode, versus 6.46 seconds on Pilot 024 and 10.55 seconds on the earlier reference. The benchmark failed the zero-loss requirement, so the fresh acceptance set stayed sealed. [Paired benchmark and generation evidence](../evidence/direct-accuracy-pilot-027.json)

Run `python examples/replay_output_row_edit.py --pilot 27 --parent PATH_TO_PILOT_024.gguf` to verify the whole saved checkpoint digest. The sparse XOR capsule changes 58 stored bytes across two 2,880-byte rows. [Patch capsule](../evidence/direct-closure-pilot-027-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Twenty-eighth pilot with held-family training

Pilot 028 used 144 independently checked development problems from 18 high-school and college math families. The 576 scored prompts showed each problem in four cyclic answer orders. Three folds kept every variant of a family together. Each fit trained on two folds, and all three patches were frozen before their held-family scores were computed. The official benchmark, accepted proof traces, and sealed fresh set stayed outside fitting. [Corpus and fit receipts](../evidence/direct-accuracy-pilot-028.json)

The packed CPU estimate and exact CUDA replay agreed on all held-family outcomes. Correct rotations rose from **342/576 to 350/576**, with 21 gains and 13 losses. Items correct in all four orders rose from **46/144 to 50/144**. College gained eight correct rotations and high school held steady. One of three folds declined overall, and one previously all-correct problem lost an order. These results describe three train-on-two-folds fits. [Per-fold and subject results](../evidence/direct-accuracy-pilot-028.json)

The all-authored fit changed 266 single-step Q4_K codes across the four answer-letter rows, occupying 264 stored bytes. The CUDA preview improved its fitting prompts from **342/576 to 358/576** with zero prior-correct losses. Readback verified the rest of the checkpoint byte for byte, including D63 and the reasoning-finish row. CPU calibration reconciled four near-half quantization codes against their unlabeled native logits and retained the same parity checks. [Final fit and readback](../evidence/direct-accuracy-pilot-028.json) · [Pinned CUDA quantizer](https://github.com/ggml-org/llama.cpp/blob/8642541b2/ggml/src/ggml-cuda/quantize.cu#L74-L89)

On a separate 32-problem authored transfer set, the saved checkpoint scored **71/128 versus 70/128** over cyclic answer orders. Three rotations improved and two regressed. Both checkpoints answered eight items correctly in all four orders. This set was held out of fitting. The saved checkpoint also reproduced all 576 preview logit vectors and both captured activation buffers bit for bit. [Transfer and saved-file replay](../evidence/direct-accuracy-pilot-028.json)

The interval proof replayed exactly. Euler completed naturally and gave the correct exact solution, verified by substitution into the differential equation and both initial conditions. Its token stream first diverged at index 504, where the parent chose edited token ` D` and Pilot 028 chose untouched token ` P`. Euler used 1,702 tokens versus the reference’s 1,340, so exact proof preservation failed. The correct cylinder answer matched byte for byte and ended at 282 tokens. It took 6.88 seconds to decode, versus 6.46 on Pilot 024 and 10.55 on the earlier reference. [Proof and cylinder evidence](../evidence/direct-accuracy-pilot-028.json)

Matched MMLU was **226/370 for both checkpoints**. Ten previous misses became correct and ten previously correct answers became wrong. High school rose from 162/270 to 163/270, while college fell from 64/100 to 63/100. Pilot 028 failed both exact proof preservation and the zero-loss accuracy requirement, so the blinded fresh set stayed sealed. [Paired benchmark results](../evidence/direct-accuracy-pilot-028.json)

Run `python examples/replay_output_row_edit.py --pilot 28 --parent PATH_TO_PILOT_024.gguf` to verify the whole saved checkpoint digest using the exact Pilot 024 model and the packed XOR deltas. [Patch capsule](../evidence/direct-closure-pilot-028-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

## Twenty-ninth pilot with a strict close-margin guard

Pilot 029 froze the B answer row and refit A, C, and D on the authored training families. For each training split, the closest quarter of prior-correct choices had to retain their original minimum lead over every rival. The original signed winner checks and 635 prior authored controls still applied.

Before adding that rule, the three folds had 1,211, 1,184, and 1,538 feasible improving single-code moves. The strict rule reduced each count to zero. Every packed row remained byte-identical to Pilot 024, with **342/576** correct rotations and **46/144** problems correct in all four orders. The guarded floating-point fit scored **339/576** and **44/144** before packing. These are exploratory measurements on the reused authored families. [Fold receipts and margin thresholds](../evidence/direct-accuracy-pilot-029.json)

On a separate free-response diagnostic, Pilot 024 solved **15/16** with correct visible derivations and natural stops. It completed all eight high-school problems and seven college problems. A college graph-walk problem reached the 3,072-token cap before emitting a visible answer. The first launch's validator rejected a default trace setting while tracing was disabled. The corrected launch reproduced the first four responses byte for byte with the same generation settings. This diagnostic stayed outside fitting, candidate selection, and acceptance. [Diagnostic and independent review receipts](../evidence/direct-accuracy-pilot-029.json)

## Pilots 030 and 031 with coupled moves and a soft margin penalty

Pilot 030 used coordinated changes to packed codes while keeping the B row exact and honoring the same signed floors as Pilot 029. All three folds produced feasible edits. Correct rotations stayed at **342/576** with three gains and three losses. Problems correct in all four orders rose from **46/144 to 47/144**. High school lost one correct rotation and college gained one. [Fold metrics and receipts](../evidence/direct-accuracy-pilots-030-031.json)

Pilot 031 retained the original signed guards and used nested training folds to choose the strength of a soft penalty for shrinking close margins. One fold fell back to the exact parent, one selected zero penalty, and one selected a weight of 0.1. Held correct rotations rose from **342/576 to 345/576** with six gains and three losses. The number of problems correct in all four orders stayed at **46/144**. Both pilots were CPU experiments on reused authored families and stopped before saving a model or running the matched benchmark. [Selection and held-family receipts](../evidence/direct-accuracy-pilots-030-031.json)

## Pilot 032 with a family-weighted loss

Pilot 032 tested a family-weighted objective that assigned more weight to families whose training loss rose as the optimizer changed the packed answer rows. The nested selector picked the unchanged parent for two folds and mean loss for one. The selected edits kept B byte-identical and passed all 4,239 signed checks in the changed fold. Held rotations fell from **342/576 to 340/576** with one gain and three losses. Problems correct in all four orders fell from **46/144 to 45/144**. Neither family-weighted setting was selected for outer scoring, so these results measure the nested selection policy. [Per-family policy and fit receipts](../evidence/direct-accuracy-pilot-032.json)

## Pilot 033 with an internal rank-three edit

Pilot 033 changed the final feed-forward down-projection, `blk.63.ffn_down.weight`. The edit uses three residual directions and keys derived from activations captured on independently authored option rotations. The fitted keys determine how strongly each input activates the edit. The output head stays byte-identical, while the changed residual can move logits across the vocabulary. The fitter removes the direct component toward the reasoning-finish output row before normalization. Exact generation still needs a separate check.

On the reused authored families, CPU replay of the three rounded F32 edits increased correct rotations from **342/576 to 348/576**, with 13 gains and seven losses. Problems correct in all four orders increased from **46/144 to 48/144**. High school gained one correct rotation and college gained five. These are exploratory scores from three separate fits.

The full-strength fit lost two previously correct training rotations when replayed through quantization. A frozen scale search picked the first positive step that kept every previously correct training choice and corrected at least one miss. At scale **0.5**, the final fit changed 89,034,485 F32 values with a relative Frobenius change of **0.0270%** in the edited tensor. Exact CUDA suffix replay on the original authored inputs confirmed **346/576** correct rotations and **47/144** all-four, with four gains and zero losses. All 2,304 parent choice logits matched the archived native values bit for bit.

The saved GGUF differs from Pilot 024 only inside D63. Reloading it reproduced all 576 preview residuals, hidden vectors, and full-vocabulary logit vectors bit for bit. Verify the exact full checkpoint digest with `python examples/replay_d63_rank_two_edit.py --pilot 33 --parent PATH_TO_PILOT_024.gguf`. The factors already include the selected scale. [Aggregate receipts](../evidence/direct-accuracy-pilot-033.json) · [Exact factor capsule](../evidence/direct-accuracy-pilot-033-d63-patch.json) · [Replay code](../examples/replay_d63_rank_two_edit.py)

Neither accepted proof replayed exactly. The interval proof first diverged at token index 286 and reached the 3,072-token cap without a visible answer. Euler first diverged at index 92 and ended naturally with a correct exact solution at 1,429 tokens, versus 1,340 on Pilot 024. The correct cylinder answer matched all 282 generated tokens and took 6.90 seconds to decode, versus 6.46 on Pilot 024 and 10.55 on the earlier reference. The proof gate blocked matched MMLU and the blinded fresh set stayed sealed. [Proof, cylinder, and qualification receipts](../evidence/direct-accuracy-pilot-033.json)

## Pilot 035 with one-sided answer-position correction

In each training split, Pilot 035 mapped the four rotations back to their original answer contents and estimated which answer position received the largest positive score offset. All three splits selected B. Their edits moved 24, 25, and 68 packed Q4_K codes in that row by one step. The A, C, and D rows stayed byte-identical.

The B score fell on all 576 held rotations. Prior-correct training winners and all 172 winners on separate authored teacher-forced states were preserved. Held accuracy moved from **342/576 to 343/576**, with four gains and three losses. All-four accuracy stayed at **46/144**. The fit missed the exploratory transfer gate and stopped before writing a checkpoint. [Fit and held-family receipts](../evidence/direct-accuracy-pilot-035.json)

## Pilot 034 with ordinary-generation guards

Pilot 034 added a separate set of 12 original open-response problems. Ten baseline responses ended naturally, and nine passed independent review for correct, complete work. The capture replayed 234 sampled token decisions exactly and retained 90 states. The fitter used those authored states to protect ordinary generation. The accepted proofs, matched benchmark, and blinded fresh problems stayed outside fitting and scale selection.

Within each split, the fitter projected the D63 input directions away from the span of the ordinary training states. It then scaled the remaining directions using only the choice training rows. Both the math families and the ordinary trajectories were held out by group. Correct rotations rose from **342/576 to 351/576**, with 18 gains and nine losses. All-four accuracy rose from **46/144 to 49/144**.

On held ordinary states, the guarded edit's relative residual change had **44.7%** of the RMS of Pilot 033's unguarded edits. The CPU approximation preserved all winners among the 64 archived contenders at each state. A separate CUDA check is required to verify winners across the full vocabulary. The final rounded CPU fit scored **362/576** correct rotations and **50/144** all-four, with 20 gains and zero training losses. [Capture, held-fold, and final fit receipts](../evidence/direct-accuracy-pilot-034.json)

CUDA confirmed both authored scores and preserved every previously correct training choice. Across the 90 reviewed ordinary states, the parent and the edited tensor chose the same archived winner from the full vocabulary. These checks replayed the captured inputs and represent individual token decisions. Complete proof generation is evaluated separately. [CUDA and trajectory receipts](../evidence/direct-accuracy-pilot-034.json)

The saved GGUF differs from Pilot 024 only inside D63. Reloading it reproduced all **666** preview residuals, hidden vectors, and full-vocabulary logit vectors bit for bit. Run `python examples/replay_d63_rank_two_edit.py --pilot 34 --parent PATH_TO_PILOT_024.gguf` to verify the complete checkpoint hash from the factors. [Saved replay evidence](../evidence/direct-accuracy-pilot-034.json) · [Factor capsule](../evidence/direct-accuracy-pilot-034-d63-patch.json) · [Replay code](../examples/replay_d63_rank_two_edit.py)

Pilot 034 repeated Pilot 033's first token divergence on each accepted proof. The product-error proof diverged at zero-based index 286 and reached 3,072 tokens without a visible answer. Euler diverged at index 92 and finished naturally with a correct solution in 1,429 tokens. The cylinder answer was byte-identical to Pilot 024 and ended naturally at **282 tokens**. Decode took 6.38 seconds versus 6.46 on Pilot 024 and 10.55 on the earlier reference. The failed proof gate blocked matched MMLU and left the blinded fresh set sealed. [Proof and cylinder receipts](../evidence/direct-accuracy-pilot-034.json)

## Pilot 036 with ordinary-winner constraints on packed answer rows

Pilot 036 fitted answer-token rows with signed constraints on the full-vocabulary winners of reviewed ordinary states. Each fold held out both math families and entire ordinary trajectories. The packed CPU estimates gained two correct rotations, **342/576 to 344/576**, with five gains and three losses. All-four accuracy rose from **46/144 to 47/144**, and none of the 90 held ordinary winners changed in the CPU screen.

The final authored fit changed 16 Q4_K codes, two in C and 14 in D. Each code moved by one step within its existing quantization block. A, B, and the block metadata stayed byte-identical. The fit scored **350/576** correct rotations and **48/144** all-four, with eight gains and zero losses on the training set. [Held-fold and final fit receipts](../evidence/direct-accuracy-pilot-036.json)

CUDA confirmed both authored scores and all 90 reviewed ordinary winners. The overlay preserved every untouched vocabulary logit and every bit of the captured residual and hidden activations. The saved GGUF differs by 16 bytes and reproduced all 666 overlay states bit for bit after reload. Verify its full hash with `python examples/replay_output_row_edit.py --pilot 36 --parent PATH_TO_PILOT_024.gguf`. [Packed XOR capsule](../evidence/direct-closure-pilot-036-row-patch.json) · [Replay code](../examples/replay_output_row_edit.py)

Both accepted proofs reproduced their full token streams and visible answers exactly. The product-error proof ended naturally at 1,628 tokens and Euler at 1,340. The cylinder answer was byte-identical and ended naturally at **282 tokens**. Its measured decode time was 6.43 seconds, versus 6.46 for Pilot 024 and 10.55 for the earlier reference. [Proof and cylinder receipts](../evidence/direct-accuracy-pilot-036.json)

Matched MMLU fell from **226/370 to 224/370**, with two recovered misses and four previously correct answers lost. High school moved from 162/270 to 161/270 and college from 64/100 to 63/100. All 370 items were scored under identical prompt order and native settings. The failed accuracy gate left the blinded fresh set sealed. [Matched benchmark receipts](../evidence/direct-accuracy-pilot-036.json)

## Pilots 037 and 038 with additional D63 constraints

Pilot 037 projected the D63 output directions away from the gradients of ordinary winner margins. The output-only fit reached **346/576** rotations and **47/144** all-four. Adding Pilot 034's input projection reached **348/576** and **49/144**. Relative to Pilot 034, the RMS movement of the seven nearest ordinary margins was 127% for the output-only fit and 92% for the combined fit. Both arms missed the preregistered reduction after adjusting for choice-logit movement. [Pilot 037 receipts](../evidence/direct-accuracy-pilot-037.json)

Pilot 038 selected input directions by comparing terminal choice activations with ordinary activations. At matched choice-edit strength, it scored **346/576** rotations and **48/144** all-four. Pilot 034's matched control scored **347/576** and **48/144**. Pilot 038 moved held ordinary residuals about 14% more than the control. None of the three D63 variants in these two pilots changed a winner in its held archived top-64 CPU check. The runs ended before native verification or checkpoint storage. [Pilot 038 receipts](../evidence/direct-accuracy-pilot-038.json)

## Pilots 039 and 040 on two authored math sets

Pilot 039 added 36 independently checked problems, split equally between high-school and college math. Each problem had four option orders. The two pilots fitted on both the earlier and expanded sets, using three splits that kept whole families and ordinary-generation trajectories together. Pilot 039 weighted the corpora equally and penalized shrinking small correct-answer margins. It moved 9, 18, and 24 packed codes across the three C and D row fits. Pilot 040 used a mixed-integer search over A, C, and D to recover near-miss training choices while retaining signed winner margins. It moved 10, 46, and 23 codes. Each code moved one step within its existing quantization block, and both pilots kept the B row byte-identical.

| Held development result | Parent | Pilot 039 | Pilot 040 |
|---|---:|---:|---:|
| Earlier set correct rotations | 342/576 | 344/576 (+5/-3) | 339/576 (+1/-4) |
| Earlier set correct in all four orders | 46/144 | 47/144 | 45/144 |
| Expanded set correct rotations | 55/144 | 56/144 (+3/-2) | 58/144 (+3/-0) |
| Expanded set correct in all four orders | 2/36 | 2/36 | 2/36 |
| Held ordinary winner changes in CPU replay | 0/90 | 0/90 | 0/90 |

Pilot 039 failed because the earlier high-school score fell from 205 to 204 and the expansion lost two previously correct rotations. Pilot 040 recovered three expansion rotations without a loss there, but lost four previously correct rotations on the earlier set. Both experiments stopped at the exploratory CPU gate. No edited checkpoint was saved or run natively. [Paired results, input hashes, and exact packed row recipes](../evidence/direct-accuracy-pilots-039-040.json)

A post-fit audit of the frozen rows found that Pilot 039 had already recovered all four rotations Pilot 040 gained across the two sets. Three rotations became incorrect in both pilots. In all nine loss occurrences, the edit raised the score of the wrong option that won, C in eight and D in one. The parent’s correct option led its strongest rival by at most 0.10 logits in eight of those nine occurrences. [Aggregate margin audit and reproduction hashes](../evidence/direct-accuracy-pilots-039-040.json)

## Pilot 041 with answer-position contrast directions

Pilot 041 fitted a D63 edit with rank at most three using activation differences between near-miss rotations and correct sibling rotations. The input directions were projected away from the earlier-set and ordinary-generation training activations. The first run stopped before held scoring when the second fold supplied only one usable answer-position transition. The revised rule allowed a single transition and retained the training guards and scale grid.

All three fits passed the rounded training checks and were frozen before held scoring. On the training states used for the projection, the largest relative residual movement was below **1.3 × 10⁻⁸**. On held families, the earlier set fell from **342/576 to 341/576** correct rotations and **46/144 to 45/144** all-four. The expanded set stayed at **55/144** correct rotations and **2/36** all-four.

All **90** held ordinary states kept their winners among the 64 archived contenders in the CPU screen. The training projection and held screen cover different states. The held development gate failed, and the run stopped before native verification or checkpoint creation. [Held-fold evidence and verified factor and tensor hashes](../evidence/direct-accuracy-pilot-041.json)

## Pilot 042 with two demonstration contexts and two option orders

The same Pilot 024 checkpoint scored 36 independently checked authored problems under four conditions. Each condition used four rotations so the correct answer appeared once at every letter. The alternate demonstration context reordered the same five examples and changed their individual answer positions while preserving each subject’s answer-letter histogram. Reversing the option cycle preserved the first and third displayed options at each rotation.

| Demonstration context | Cyclic option order | Reversed cyclic option order |
|---|---:|---:|
| Original | 55/144 | 68/144 |
| Alternate | 71/144 | 68/144 |

Changing the examples at cyclic order recovered 20 choices and lost four. At reversed order it recovered 15 and lost 15. The effect of reversing the option cycle changed from a gain of 13 with the original examples to a loss of three with the alternate examples. Paired by problem and correct answer letter, reversing the cycle changed the selected answer content on 65 of 144 trials with the original examples and 66 of 144 with the alternate examples. Only two of 36 problems were correct in every one of the 16 presentations. Keeping the correct letter fixed, the parent answered 44 of its 89 original misses correctly in at least one other condition. It lost 19 of its 55 original correct choices in at least one other condition.

The comparison used 432 new CUDA scores and 144 archived scores whose prompt bytes matched exactly. It measured prompt sensitivity on reused development families at fixed weights. [Factorial results and provenance](../evidence/direct-accuracy-pilot-042.json)

## Pilot 043 with a penalty for answer-position drift

Pilot 043 mapped each centered logit shift back to its original answer content and penalized disagreement across the four rotations of the same problem. A separate term penalized the average shift for each displayed letter. The fit used one-step packed-code edits in rows A, C and D and kept B byte-identical. The three frozen folds changed 11, 24 and 31 codes.

On the expanded held set, the edit improved from **55/144 to 57/144** with two gains and zero losses. On the earlier held set it fell from **342/576 to 340/576**, with one gain and three losses. All three losses also occurred in Pilot 040. All 90 held ordinary winners were preserved in both the float64 and binary32 CPU replays. The older losses failed the frozen gate, so the trial ended at CPU evaluation. [Held metrics and exact packed-row recipes](../evidence/direct-accuracy-pilot-043.json)

## Pilot 044 on new factorial development families

Pilot 044 added 48 original problems across 12 high-school and college families. Independent solvers agreed with all 48 author keys. Each problem appeared in both demonstration contexts and both option orders from Pilot 042, with four rotations per condition. All 768 native scores came from Pilot 024. An independent replay checked all 3,072 binary32 choice logits against the graded baseline.

| Demonstration context | Cyclic option order | Reversed cyclic option order |
|---|---:|---:|
| Original | 104/192 | 95/192 |
| Alternate | 95/192 | 90/192 |

The alternate context lowered the score on this corpus, after increasing it at cyclic order in Pilot 042. Only eight of the 48 new problems were correct in all 16 presentations. When pairing the same problem and correct displayed letter, the original-context reversal changed the selected answer content on 89 of 192 trials. Twenty missed presentations had correctly answered counterparts spanning both demonstration contexts and both option orders. These give a direct edit examples of context-dependent errors with the answer letter held fixed. [Parent baseline, paired outcomes, and exact receipt hashes](../evidence/direct-accuracy-pilot-044-baseline.json)

## Pilots 045 and 046 on the factorial families

Pilot 044's activation capture matched all 3,072 baseline choice logits exactly. Pilot 045 fitted a rank-at-most-three edit to the final feed-forward tensor. For each targeted miss, it used correct presentations of the same problem with the correct answer in the same position. The fit compared the same incorrect answer content across permutations. In two folds, the CPU replay with Q8 activation quantization violated a signed training margin floor at every scale that recovered a training answer. Those folds sealed zero edits. The remaining fold passed its training checks and recovered one training answer. Held scores were identical to the parent across all three math sets, and all 90 ordinary winners stayed identical among the archived top 64.

Pilot 046 changed 28, 82 and 29 packed codes across its three fits. It penalized disagreements in the shift of the same answer content across presentations and relative erosion of the missed presentation's margin. The new held set moved from **384/768 to 383/768**, with one gain and two losses. The earlier 028 set stayed at **342/576**, with two gains and two losses. The 039 set stayed at **55/144**. All 90 held ordinary winners were preserved in the reduced full-vocabulary CPU replay. The four lost math answers had led by **0.0062 to 0.0257 logits** before editing. Two flipped to A and two to D.

Both methods stopped at the held development gate. The fold artifacts preserve the direct edits and their exact replay hashes. [Capture pins, held scores, and fold recipes](../evidence/direct-accuracy-pilots-045-046.json)

## Pilots 047 and 048 on quantization and close margins

Pilot 047 used the observed difference between the linear margin prediction and the CPU Q8 replay to tighten constraints locally. All 15 refinements satisfied their linear constraints, and all 15 violated at least one original margin floor in the quantized replay. Fold 0 kept the same rounded tensor edit as Pilot 045. Folds 1 and 2 kept the parent tensor. All held math scores and all 90 archived top-64 ordinary winners were preserved.

Pilot 048 protected the native winner on close, non-target training choices, including those the parent answered incorrectly. It bounded the edit's margin effect under componentwise variation estimated from the four same-letter contexts. The three fits checked 53, 45, and 62 added comparisons and passed their exact decoded bounds. On held data, the earlier 028 score moved from **342/576 to 340/576**, the 039 score moved from **55/144 to 56/144**, and the 044 score stayed at **384/768**. Two incorrect choices on 044 switched to a different incorrect answer. All 90 ordinary full-vocabulary winners stayed exact in the CPU replay.

Both trials failed their held development gates. [Fold recipes, replay hashes, and paired results](../evidence/direct-accuracy-pilots-047-048.json)

## Pilots 049 to 051 on training safety and family transfer

Pilot 049 used the CPU Q8 replay as a search objective. It tested 93 factorized proposals and accepted five steps after rounded-F32 replay confirmed every signed training guard and the ordinary controls. One fold's selected D63 edit recovered one training answer. The held accuracy was unchanged in every cohort.

Pilot 050 ranked exact packed code moves in two disjoint training-family blocks per outer fold, then considered only signed moves that both blocks supported. The three intersections contained 174, 157 and 221 moves. Under the frozen training guards, the fitter changed one packed code in one fold. Held accuracy and the 90 ordinary full-vocabulary winners were preserved.

Pilot 051 used semantic teacher margins across all three authored sets, with 77, 67 and 88 eligible training misses in its three folds. The candidate scales were checked against CPU Q8 logits. All 30 scales failed the training gate, so all three folds replayed the parent. None of these trials reached the required held gain. [Exact fold hashes, packed recipe, and paired results](../evidence/direct-accuracy-pilots-049-051.json)

## Pilot 052 with quantized-gradient descent

Pilot 052 used the measured CPU Q8 loss to propose full-gradient moves. It accepted eight steps after exact rounded-F32 replay, including six projected gradient steps. Every accepted step passed the signed training floors and ordinary controls.

On held data, the 039 score rose from **55/144 to 56/144**. The 044 original-demo cyclic arm fell from **104/192 to 102/192**, and the other three arms stayed at their parent scores. All 90 archived top-64 ordinary winners were preserved. An independent replay reproduced all 1,488 held comparisons and both nonzero tensor hashes. The two lost choices had parent correct-answer margins of **0.0088** and **0.0234** logits. One repeated a loss from Pilot 046. The two losses failed the held gate. [Paired results and margin audit](../evidence/direct-accuracy-pilot-052.json)

## Pilot 053 with a single mathematical condition changed

Pilot 053 introduced 24 original problem pairs across 12 high-school and college math families. The two variants in each pair share identical choices and differ only in one marked mathematical condition. Independent derivations agreed with all 48 exact keys, and every condition change altered the correct option. Both variants stayed in the same family fold.

Under four prompt conditions and four rotations per condition, Pilot 024 scored **327/768**. It answered both variants correctly on **42/384** aligned presentations, including **31/192** at high-school level and **11/192** at college level. It selected the same original answer content for both variants on **270/384** presentations even though the correct answer changed. Six of 48 individual problems were correct in all 16 presentations. The independent replay matched all 3,072 binary32 logits and reconciled all 384 pairs. [Exact parent results and audit](../evidence/direct-accuracy-pilot-053-paired-baseline.json)

The instrumented CUDA run captured the final feed-forward input, gate, up projection, and gated activation for all **768 states**. A separate audit mapped every state to its frozen input and reproduced all **3,072** choice logits bit for bit against the original scorer. Across the captured activations, the maximum absolute difference between the native gated activation and the independently calculated `SiLU(gate) × up` was **6.31 × 10⁻⁶**. [Full capture counts, checksums, and tolerance](../evidence/direct-accuracy-pilot-053-augmented-capture.json)

## Pilot 054 with a condition-contrast down-projection edit

Pilot 054 fit a rank-three edit to the activation differences between variants of the same authored problem. It projected out ordinary trajectory states and differences attributable to demonstration and answer order. Across three family-held folds, seven of 78 proposals passed exact rounded-tensor replay and preserved the signed training margins. The three proposals that recovered a training pair each crossed two to nine signed margins. The largest weight change that passed exact training replay was **0.00350%** of the parent tensor's Frobenius norm.

All three frozen held patches contained only zero coefficients, so the held result of **42/384** both-correct pairs is the unchanged parent result. The run stopped before native checkpoint qualification. [Fold checksums, margin violations, and held results](../evidence/direct-accuracy-pilot-054-condition-contrast.json)

## Pilots 055 and 056 with a gated up-projection edit

Pilot 055 captured the final feed-forward input, gate and up projections on four authored states. Adding those readbacks reproduced all 16 choice logits and all four original A/P/R/H activation arrays byte for byte. The CPU Q8 estimate of 68 sampled parent up-projection rows differed from native CUDA by at most **5.47 × 10⁻⁷**.

Pilot 056 incremented one Q4_K code on the CUDA device in an isolated process and read back the exact edited row. The input, gate and pre-feed-forward residual remained byte-identical. Only the targeted neuron changed in the up and gated activation arrays. The measured up change agreed with the CPU estimate to **8.78 × 10⁻⁸** and the gated change to **6.94 × 10⁻⁹**. The largest choice-logit change was **0.000353**, and the four choices stayed the same. The source GGUF passed its full before-and-after hash check. [Exact one-byte recipe, native receipts, and response errors](../evidence/direct-accuracy-pilots-055-056-up-projection.json)

With the exact Pilot 024 parent GGUF and Python 3.11 or later, run `python prototypes/verify-pilot056-packed-row.py <parent.gguf>` from the repository root. The verifier hashes the entire source, reconstructs the edited row in memory, and checks the published digest. This command reproduces the packed byte change. The recorded activation changes came from the separate CUDA replay. [Read-only verifier](../prototypes/verify-pilot056-packed-row.py)

## Pilots 057 and 058 with signed packed up-projection edits

Pilot 058 replayed **90 positions across nine independently reviewed ordinary solutions**. The added upstream readbacks preserved all 90 archived winners, 5,760 top-64 logits, 540 selected logits, and the original activation arrays exactly.

Pilot 057 used those controls and searched **33** direct edits to Q4_K codes in the final up projection across three training folds. Seven proposals improved paired answers while preserving every previously correct training choice. Each still crossed a signed margin floor, with three to seven violations per proposal. All frozen held patches were numerical no-ops. The both-correct score stayed at **42/384**, and no checkpoint was written. [Search tradeoffs and ordinary replay](../evidence/direct-accuracy-pilots-057-058-packed-up.json)

## Pilot 059 with a multi-row CUDA edit

The generalized CUDA patcher applied three signed Q4_K code changes across two rows on four authored states. Readback verified both edited rows exactly. Only the two targeted neurons changed in the up and gated activation arrays. The input, gate, pre-feed-forward residual, and source file matched their original bytes. The largest choice-logit change was **0.001131**, and all four choices stayed the same.

The largest difference between the predicted and observed residual change was **2.23 × 10⁻⁵**. Two coordinates exceeded the initial absolute tolerance. The audit reports an additional allowance of half a binary32 spacing at each endpoint, since the comparison subtracts two separately rounded native residuals. [Exact code changes and CUDA audit](../evidence/direct-accuracy-pilot-059-multirow-cuda-fixture.json)

## Pilot 060 with paired answer-margin attribution

On the same 384 aligned presentations, changing the mathematical condition moved the two relevant answer logits in the intended direction **291** times. It changed which of those two answers led in the intended direction **72** times. On 30 of those 72 presentations, another option still prevented both correct answers from winning. Across the five traced activation stages, the mean relative change induced by the condition was **47–49%** of the change induced by a cyclic option rotation.

A local decomposition of the two-answer logit gap estimated a mean **−0.423** contribution from the up branch, **+0.252** from the gate branch, and **+1.594** from the attention residual. The up and gate terms pointed in opposite directions on **242/384** presentations. These are local contributions on the authored pairs. The audit includes family-level uncertainty and CPU reconstruction error. [Paired effects, attribution, and limitations](../evidence/direct-accuracy-pilot-060-condition-alignment.json)

## Pilot 061 with compensating packed-code changes

Pilot 061 evaluated 1,269 single moves and 536 combinations on the training folds. Some combinations passed the original margin floors even when a component failed by itself. On held families, the original-floor fit gained two choices and lost one, with both-correct unchanged at **42/384**. The fit that required only a small positive margin gained five choices and lost three, with both-correct at **43/384**. Both retained the 90 ordinary winners among the archived top 64. The regressions stopped both fits before native qualification. [Frozen fold results and margin tradeoffs](../evidence/direct-accuracy-pilot-061-compensating-packed-up.json)

## Pilot 062 with smaller up-projection gain steps

Pilot 062 changed the FP16 `d` coefficient by one representable step in selected Q4_K blocks, holding the other block fields fixed. The largest predicted up response among shortlisted moves was **10.8%** of the local unit-nibble peak. Fourteen of 160 CPU proposals improved the objective while preserving the training guards. None recovered a paired training answer. The three folds froze numerical no-ops, with **42/384** both-correct on the held pairs. [Packed gain search and held results](../evidence/direct-accuracy-pilot-062-up-block-gain.json)

## Pilot 063 with feed-forward activation swaps

The CPU counterfactual replaced one or both final feed-forward branch activations with the corresponding activations from a paired state. It held the recipient's attention residual fixed and compared all four answer choices after recomputing the remaining layers. The unchanged control matched all **3,072** native choice logits bit for bit. Changes to unseen quantization boundaries and CUDA accumulation remain estimates.

| Donor | Replaced activation | Correct choices out of 768 | Both correct out of 384 |
| --- | --- | ---: | ---: |
| Unchanged control | None | 327 | 42 |
| Opposite condition | Up | 362 | 70 |
| Opposite condition | Gate | 324 | 44 |
| Opposite condition | Both | 345 | 59 |
| Next option rotation, same condition | Up | 325 | 41 |

The opposite-condition up swap recovered 44 previously missed choices and lost nine previously correct choices. It recovered 32 both-correct presentations and lost four. The swap used a paired donor activation at inference time and wrote no weights. [Intervention counts, exact parent control, and limitations](../evidence/direct-accuracy-pilot-063-ffn-interchange.json)

## Pilot 064 with a packed fit to helpful up-swap responses

Pilot 064 recomputed helpful donor responses within each training fold. It fit the up projection to those responses after projecting out ordinary inputs, then reconstructed legal Q4_K code changes with the original scale metadata. Across the 48 tested candidates, 43 recovered a training pair. Three of those preserved every correct training choice. All 48 still crossed at least one signed margin floor. The three held patches contained no changes. [Per-fold packed fit and held results](../evidence/direct-accuracy-pilot-064-up-swap-target-fit.json)

## Pilot 065 with native up-activation interchange

The CUDA replay replaced only the transient up activation on 16 states from eight preregistered authored pairs. The recipient input, gate, attention residual, and original up activation matched the archive byte for byte. The CPU prediction and CUDA replay agreed on all 16 choice winners. The largest choice-logit error was **0.000143**. The native mean intended-answer gap increased by **0.374**, and accuracy stayed at **6/16**. The source checkpoint passed its full before-and-after hash check.

The original grader assumed A–D list order. The CPU regrade verified all six expected token IDs and recovered the A–D order from those IDs in the same archived CUDA output. [Native and regrade receipts](../evidence/direct-accuracy-pilot-065-native-up-interchange.json)

## Pilot 066 with a bulk CUDA verifier

A pinned trajectory manifest passed a single CPU preflight for all **768** frozen sequences. A separate four-state CUDA fixture verified that the bulk input path reproduced the previous multi-row CUDA patch's activations, top-64 and selected logits byte for byte. [Preflight and CUDA parity checksums](../evidence/direct-accuracy-pilot-066-bulk-native-parity.json)

## Pilot 067 with jointly constrained up codes

Pilot 067 added all prior-correct 044 margins to the 053 training constraints. It solved a continuous margin problem and selected integer Q4_K changes on a bounded support. The first run stopped after two no-op folds when the integer solver timed out with fractional code values. A separate rerun preserved the fit settings, recorded the invalid vector and discarded it.

Of **40** distinct nonzero proposals, **18** recovered a training pair. All 40 violated a signed 053 floor, and 39 also violated a signed 044 floor in exact rounded CPU replay. All three held folds kept the original weights. The paired result stayed at **42/384**, and the 90 ordinary winners stayed unchanged among the archived top 64. [Solver recovery, held results, and independent audit](../evidence/direct-accuracy-pilot-067-guarded-packed-up.json)

## Pilot 068 with read-only upstream capture on the 044 cohort

The CUDA capture added the final feed-forward input, gate and up activations for all **768** existing 044 states. An independent CPU audit matched all **3,072** binary32 choice logits against both the archived terminal capture and the original scorer. It also matched the 768 top-64 ledgers and full-vocabulary winners, and verified the original A, P, R, H and gamma arrays byte for byte. The largest absolute difference between the stored gated activation and the reconstructed SwiGLU output was **7.93 × 10⁻⁶**. The source checkpoint passed its full before-and-after hash check. [Capture and independent audit checksums](../evidence/direct-accuracy-pilot-068-044-upstream-capture.json)

## Pilot 070 with a continuous gate and up comparison

The fixed comparison used the same twelve neuron slots for the up-only, gate-only and joint lanes. It imposed both the original signed margin floors and a separate positive-margin control on the 053 and 044 training states. It replayed each frozen fit with anchored FP32 activations and CPU Q8 output. These were continuous coefficients, with no code packing or checkpoint write.

| Branch | Training guard | Held 053 paired gains and losses | Held prior-correct losses, 053 and 044 |
| --- | --- | ---: | ---: |
| Up | Signed | 0 / 1 | 1 / 5 |
| Gate | Signed | 0 / 1 | 1 / 2 |
| Joint | Signed | 0 / 1 | 2 / 6 |
| Up | Positive | 2 / 1 | 4 / 6 |
| Gate | Positive | 2 / 2 | 6 / 5 |
| Joint | Positive | 3 / 2 | 8 / 7 |

Every lane preserved the 90 held ordinary winners among the archived top 64. Each signed lane still crossed training floors after Q8 replay. The held families were grouped within each corpus. The independently authored complex-analysis sets share a family label and fall in different source-local folds. [Frozen method and per-fold results](../evidence/direct-accuracy-pilot-070-branch-capacity.json)

## Pilot 071 with output-head compensation

Pilot 071 regenerated 48 training-only up-projection proposals and considered small A–D output-head edits to restore the signed margins. The exact ordinary comparison included A–D even when those tokens were outside the original top 64. The training folds excluded family labels held in either authored corpus.

Nine of twelve head solves were infeasible within their selected coordinates. Three timed out without an incumbent. All three folds kept the parent weights. The held results stayed at **42/384** both-correct pairs, **327/768** correct 053 choices and **384/768** correct 044 choices. All 90 ordinary winners stayed unchanged in the comparison set. [Frozen fit and solver disposition](../evidence/direct-accuracy-pilot-071-joint-up-head.json)

## Pilot 072 with a targeted pair margin

Pilot 072 selected six close training pairs and optimized the minimum of their six correct-answer margins. Across 15 bounded integer solves, it ran 11 exact packed replays. One proposal moved its target minimum margin from **−0.09344** to **+0.04265** and crossed ten signed floors. After re-anchoring to the exact replay, the next proposal preserved those floors and left the target margin at **−0.00578**. All three frozen held fits contained no changes. [Frozen target search and exact replay results](../evidence/direct-accuracy-pilot-072-target-first-up.json)

## Pilot 073 with joint semantic supervision

Pilot 073 used condition-pair targets from 053 and same-letter targets from 044 in the same up-projection fit. A family held in either corpus was excluded from both training corpora. The first fold passed the exact training margins and ordinary checks with **347** code changes across **20** rows. An independent audit reconstructed every changed row and verified that all quantization metadata stayed byte-identical. The other two folds kept the parent weights.

In the grouped CPU replay, both-correct held pairs rose from **42/384 to 43/384**. The edit lost one previously correct 053 choice and two 044 choices, with zero ordinary winner changes among the archived top 64. The 053 loss had led its later winner by **0.12033** logits in the parent. The two 044 leads were **0.01709** and **0.01026**. The holdout gate failed and no edited checkpoint was written. [Frozen plan, packed-row audit, and held tradeoffs](../evidence/direct-accuracy-pilot-073-joint-semantic-up.json)

## Pilot 074 with native replay of the rejected fold

The exact 347-code overlay replayed all **542** held states from Pilot 073's edited fold on CUDA. The CPU and CUDA agreed on every one of the **512** math choices, including all three regressions, and all **30** ordinary winners. The largest choice-logit difference was **0.000834**. CUDA reproduced the paired gain from **15 to 16 out of 128** in the edited fold. This run was diagnostic and produced no checkpoint. [Native and CPU comparison](../evidence/direct-accuracy-pilot-074-native-rejected-fold-replay.json)

## Pilot 075 with upstream capture on two older authored cohorts

The pinned CUDA reader captured **576** states from Pilot 028 and **144** from Pilot 039. Independent checks matched all **2,880** archived A–D logit bit patterns, every full-vocabulary winner, every top-64 ledger, and all five tensors available for byte-for-byte comparison. The audit preserved each source's original family assignments. Five exact family labels had different fold assignments across the two sources, so a later joint fit had to exclude a label from training whenever either source held it out. [Native capture and independent audit](../evidence/direct-accuracy-pilot-075-older-upstream-capture.json)

## Pilot 076 with Q8 rounding-cell guards

Pilot 076 used a positive winner margin floor and required exact preservation of selected Q8 blocks on the closest training winners. Its integer solve included linear constraints for the block maximum, signed rounding boundaries and FP16 scale. A synthetic check preserved codes and scale on **200** points inside the constructed cells. Exact rounded CPU replay remained the gate for actual packed proposals.

Of **29** exact packed proposals, **17** recovered a training pair. One proposal preserved every selected block and recovered no training pairs. The held evaluation kept the parent weights in all folds. [Frozen cell guards and packed replay](../evidence/direct-accuracy-pilot-076-q8-cell-up.json)

## Pilot 077 with lower-conflict training targets

The search evaluated **29** packed up-projection proposals. Nine recovered at least one training pair, and each lost a previously correct training choice. The closest proposal gained one pair, lost one choice, and crossed six signed margin floors. The rule for this run required every correct training choice to survive before head compensation. All three folds kept the parent weights. [Training search and held checks](../evidence/direct-accuracy-pilots-077-080-lower-conflict-joint.json)

## Pilot 078 with four authored training cohorts

The fit used condition pairs from 053 and same-letter pairs from 044, with additional choice guards from 028 and 039. Any exact family label held out in one source was excluded from all four training sources. One fold passed the training gates with **96** code changes across **12** up-projection rows. Its both-correct training pairs rose from **27 to 30**, with all four cohorts preserving previously correct choices and their required positive margins.

In grouped held replay, both-correct pairs rose from **42/384 to 44/384** with no pair losses. Individual choices still regressed across the four sources. Pilot 053 went from **327 to 328** correct with two losses, 044 from **384 to 380** with nine losses, 028 stayed at **342** with one loss, and 039 stayed at **55** with zero losses. All **90** ordinary winners stayed fixed. The candidate failed the held choice gate. These are repeated authored development folds. No official or fresh evaluation ran. [Four-corpus fit and held outcomes](../evidence/direct-accuracy-pilot-078-four-corpus-up.json)

## Pilot 079 with same-letter activation swaps

This CPU diagnostic swapped feed-forward activations between matched 044 contexts that had the same correct answer letter. It varied the demonstrations or the option order while holding the other factor fixed. The zero-swap control reproduced all **3,072** A–D logits. Across **768** option-order recipient states, swapping the gate moved accuracy from **384 to 391** correct and moved both-correct pairs from **133 to 152 out of 384**. Swapping the up branch moved the counts to **333** and **97**, respectively. Swapping both branches moved them to **365** and **116**. The gate intervention gained 39 individual choices and lost 32.

Where donor content and donor letter predicted different changes, the up branch followed donor content in **26/34** changed cases and donor letter in **1/34**. The gate followed donor letter in **21/38** and donor content in **9/38**. The remaining changes followed neither. Demonstration swaps yielded **382** correct for up, **371** for gate, and **375** for both. This intervention used captured native activations as anchors and changed no weights. [Swap controls and aggregate outcomes](../evidence/direct-accuracy-pilot-079-same-letter-context-swap.json)

## Pilot 080 with head compensation after a temporary training loss

The follow-up allowed the head solver to receive an intermediate proposal with one training choice loss and up to ten signed-margin deficits. Seven packed head-code changes across four output rows repaired all **1,461** protected signed training margins for one fold. The joint edit improved the fold's both-correct training pairs from **27 to 28** and preserved every correct training choice.

Grouped held pairs rose from **42/384 to 43/384**. Individual choices still regressed. Pilot 053 gained three and lost one, moving from **327 to 329**. Pilot 044 gained five and lost four, moving from **384 to 385**. All **90** ordinary winners held, including coverage of **348** answer-token comparisons outside the archived top 64. The joint edit failed the held choice gate and produced no checkpoint. [Joint fit and held checks](../evidence/direct-accuracy-pilots-077-080-lower-conflict-joint.json)
