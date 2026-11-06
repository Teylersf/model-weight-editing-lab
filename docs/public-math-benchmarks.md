# Public math benchmarks

We froze the saved Windows rank-two checkpoint before running these public evaluations. E10 is the preceding accepted research checkpoint. The Huihui GGUF is the vendor checkpoint from before the lab's edits. Their file hashes identify the exact models used locally. [Windows qualification and checkpoint hashes](../evidence/experiment-summary.json)

## MMLU answer selection

We use the entire `high_school_mathematics` and `college_mathematics` test splits, with 270 and 100 questions respectively. Each raw prompt uses the five official development examples for its subject and ends with `Answer:`. We take the highest next-token logit among the four leading-space answer tokens. The original evaluator used a legacy completion API with a top-100 fallback. This run observes all four logits directly and uses no generated explanation. [Original data and evaluator](https://github.com/hendrycks/test/tree/4450500f923c49f1fb1dd3d99108a0bd9717b660)

The test denominator includes every question. Invalid and censored cases are reported separately and count as incorrect. Combined accuracy gives equal weight to every question. A paired comparison reports questions each checkpoint uniquely got right, so equal totals can still show changes. These public splits may overlap the upstream model's training data. Scores describe these benchmark questions, with no conversion to school grades or student percentiles.

| Full test split | Original Huihui | E10 | Windows rank-two |
| --- | ---: | ---: | ---: |
| High school mathematics | 159 / 270 (58.9%) | 160 / 270 (59.3%) | 162 / 270 (60.0%) |
| College mathematics | 64 / 100 (64.0%) | 64 / 100 (64.0%) | 64 / 100 (64.0%) |
| Combined | 223 / 370 (60.3%) | 224 / 370 (60.5%) | 226 / 370 (61.1%) |

All three checkpoints produced valid logits on all 370 questions, with zero prompt limit hits and zero ties. Rank-two corrected two high-school answers compared with E10 and three compared with original Huihui. It preserved every correct answer from both references. All three checkpoints selected identical answers on all 100 college questions. The published preparation and grading script reproduced all three scores against the archived CUDA outputs. [Scoring source and rerun commands](../prototypes/windows-cuda-mmlu-math/README.md) · [Aggregate receipt](../evidence/public-math-benchmarks.json)

## Worked solutions

The school sample uses 16 text questions from the released AGIEval exam corpus. It contains eight SAT Math multiple-choice questions, four Gaokao math multiple-choice questions, and four Gaokao math fill-in questions. Before inference, we selected by hash within each source and four text-derived topic groups covering geometry and trigonometry, data and probability, advanced mathematics, and algebra and other topics. The topic groups use local text heuristics. [AGIEval v1.1 release](https://github.com/ruixiangcui/AGIEval/tree/84ab72d94318290aad2e4ec820d535a95a1f7552/data/v1_1)

The college sample uses one hash-selected open-response stem in each of eight UGMathBench subjects, with all three randomized variants for each stem. It covers abstract algebra, single-variable and multivariable calculus, complex analysis, differential equations, linear algebra, probability, and statistics. We report both variant-level performance and the number of stems whose three variants all pass. Variants from the same stem are related, and this diagnostic uses only eight stems. [UGMathBench paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c3af3531df85264decc31382cb319781-Abstract-Conference.html) · [Pinned release](https://huggingface.co/datasets/UGMathBench/ugmathbench/tree/8ab16f0c131a9b3b52195e64175cb5a8f3881bbf)

Worked runs use ordinary greedy CUDA decoding with the same inputs across checkpoints, an 8,192-token context, and a 6,144-token generation limit. The grading tracks the final result, valid and complete visible working, natural completion, and repeated work separately. Token counts and decode time are compared among correct, complete solutions. The small, text-only samples cover specific exam and coursework tasks. They leave coverage of images, wider curricula, and student interactions to separate evaluation. [Frozen protocol hashes](../evidence/public-math-benchmarks.json)

### AGIEval school results

| Measure | E10 | Windows rank-two |
| --- | ---: | ---: |
| Correct final answer | 15 / 16 | 14 / 16 |
| Correct answer with complete valid working | 14 / 16 | 14 / 16 |
| Natural ending | 15 / 16 | 14 / 16 |
| Token limit reached without a visible answer | 1 / 16 | 2 / 16 |
| Serious unproductive repetition | 1 / 16 | 2 / 16 |

Codex reviewed all 32 visible responses with checkpoint names hidden and froze the grades before unblinding. Both checkpoints gave complete solutions to the same eight SAT items, three Gaokao multiple-choice items, and three Gaokao fill-in items. Both reached the limit without a visible answer on the same geometry item. On a second item, E10 selected the correct answer using a false general inequality, while rank-two repeated its working until the token limit. [Aggregate receipt](../evidence/public-math-benchmarks.json)

Across the 14 paired problems where both produced correct, complete solutions and ended naturally, the median was 333 tokens and 8.11 seconds of decoding for E10, versus 321.5 tokens and 8.01 seconds for rank-two. These medians describe only the paired completions. The table retains both censored runs.

### UGMathBench college results

| Measure | E10 | Windows rank-two |
| --- | ---: | ---: |
| Pinned rule checker, all blanks, `1e-8` precision | 10 / 24 | 10 / 24 |
| Pinned rule checker, all blanks, CLI default `1e-3` precision | 14 / 24 | 14 / 24 |
| Mathematically correct final answers at displayed precision | 20 / 24 | 19 / 24 |
| Correct visible derivation and final answers at displayed precision | 17 / 24 | 16 / 24 |
| Complete worked solution meeting the full prompt | 13 / 24 | 14 / 24 |
| All three variants of a stem met the full prompt | 3 / 8 | 3 / 8 |
| Natural ending | 20 / 24 | 20 / 24 |
| Token limit reached without a visible answer | 4 / 24 | 4 / 24 |
| Serious unproductive repetition | 4 / 24 | 5 / 24 |

Codex reviewed all 48 responses with model names hidden before seeing the rule results. The full-prompt grade required a correct and complete visible derivation, relevant conditions and exact requested answers, valid native output format, and no serious repetition. The rule checker measures agreement with the released reference values. The post-review check at the CLI default accepted four additional exact answers for each model where the reference was rounded. Equivalent generators of the same ideal were still rejected when their numeric values differed. All four censored responses per checkpoint counted as incorrect in every accuracy row. [Pinned rule checker](https://github.com/YangLabHKUST/UGMathBench/blob/df47bfa639bfb89bdb0220036a7b2f216e72b0b3/judge_rule.py) · [CLI defaults](https://github.com/YangLabHKUST/UGMathBench/blob/df47bfa639bfb89bdb0220036a7b2f216e72b0b3/eval_rule.py) · [Aggregate receipt](../evidence/public-math-benchmarks.json)

Both checkpoints met the full prompt on all three variants of the multivariable calculus, complex analysis, and linear algebra stems. On the 12 paired variants where both met the full prompt and ended naturally, median generation was 519 tokens and 12.89 seconds of decoding for E10, versus 572.5 tokens and 14.40 seconds for rank-two. This sample shows remaining failures in choosing an answer, valid visible working, and exact final formatting.

## First repair pilot on the known failures

A rank-five edit of the saved D63 feed-forward matrix targeted five decisions found in the original worked responses. The new tensor changed by 4.18% of its parent's tensor norm. Independent readback confirmed that the rest of the GGUF was byte-identical. Each intended token won against the full vocabulary in a CUDA check using the rounded edit.

Ordinary generation repaired the ideal-intersection error, added the missing differential-equation derivation, and printed the correct exact Bayes result. Both targeted statistics responses ended naturally, at 435 and 301 tokens versus 6,144 and 4,168 in the parent. Both statistics answers still failed the complete-math review because of numerical or precision errors. The two accepted interval and Euler proofs reproduced exactly. These are known development cases used to design the edit. Broader benchmark and fresh evaluation results are tracked separately. [Checkpoint and review receipts](../evidence/public-math-benchmarks.json)

The pilot scored 162 of 270 on high-school MMLU and 64 of 100 on college MMLU, tying its parent. It gained one high-school answer and lost one. All college choices matched the parent. The repair fit did not use MMLU answer keys or examples. [Matched MMLU receipt](../evidence/public-math-benchmarks.json)

## Second repair pilot

The next pilot directly edited the same saved D63 matrix using eleven target states and 11,272 preservation states. The tensor norm changed by 7.85% relative to the accepted parent. Independent readback verified that every byte outside the tensor matched, and all eleven desired tokens won against the full vocabulary in the rounded CUDA preview.

Ordinary generation fully repaired four of the eight known development cases: both targeted ideal operations problems, the differential-equation derivation, and the exact Bayes answer. Both archived critical proofs reproduced exactly. The three targeted statistics variants still fell short: one made an arithmetic error, one supplied rounded values where exact answers were required, and one reached the limit without a visible answer. The Gaokao inequality selected the correct option and ended naturally, but its derivative argument was invalid. These development cases informed the edit.

On the same 370 MMLU items, the pilot scored **227/370 (61.4%)**, up one from the accepted parent. High-school math rose from 162 to 163 out of 270; college math stayed at 64/100. There was one newly correct answer and no newly incorrect answers. The fit did not use MMLU examples or keys. This small measured gain and the worked repairs do not establish a broad improvement. The accepted checkpoint stayed in place. [Checkpoint, review, and paired score receipts](../evidence/public-math-benchmarks.json)

## Third repair pilot: saved weights

This pilot combined 281 repair decisions across twelve known worked failures into one direct D63 edit. It also protected 11,729 recorded states, including 10,843 from the earlier checkpoint qualification. The selected new preservation states include low-margin decisions and the earlier points where the preceding pilot drifted from the intended solution. The target decisions came from exact, reviewed replays of the known failures.

All 281 desired tokens won in a full-vocabulary CUDA check after float32 rounding. The smallest winning margin was 1.13 logits. The edited matrix changed by 39.50% of its parent's norm. Independent readback verified the saved GGUF and exact byte equality outside D63. These are checks of the stored edit and its behavior at fixed states. Whether an unforced run reaches those states and produces a complete solution is a separate test. The checkpoint remains experimental. [Checkpoint and fit receipts](../evidence/public-math-benchmarks.json)

On unforced generation, Codex found **7 complete solutions out of 12 known failures**: both ideal operations cases, the differential equation, exact Bayes, and all three statistics variants. All twelve answers ended naturally, compared with six in the parent. The statistics responses finished at 648, 317, and 438 tokens, versus 6,144, 4,168, and 6,144. Both critical regression proofs reproduced their original token sequences exactly.

The two Gaokao problems reached their correct final answers. The inequality left one comparison without rigorous error bounds, and the cube solution omitted the proof that its list was exhaustive. The three calculus variants reached an answer but still made numerical errors. The full worked score counts all five as incorrect. These are development cases used in the edit. [Ordinary generation and review receipts](../evidence/public-math-benchmarks.json)

The same 370-item MMLU replay scored **225/370 (60.8%)**, down one from the parent and two from the second pilot. High-school math was 161/270; college math remained 64/100. One item became correct and two became incorrect relative to the parent. The larger edit has the better worked development result, while the second pilot has the higher matched MMLU score. The accepted checkpoint stayed in place. [Paired benchmark receipts](../evidence/public-math-benchmarks.json)

## Fourth repair pilot: protect the entire solution path

This rank-eleven edit protected every recorded native decision in all three statistics solutions and the Gaokao inequality, alongside the other preservation states, for a total of 14,838. All eleven target tokens won the rounded CUDA check. The D63 matrix changed by 21.25% of the accepted parent's norm, with exact readback outside the matrix.

Codex verified complete, unforced solutions for **all eight targeted development problems**. This includes both ideal operations cases, the differential equation, exact Bayes, all three statistics variants, and the Gaokao inequality. The inequality now justifies both comparisons with exact bounds. Both critical proofs reproduced their original native token sequences. [Checkpoint and review receipts](../evidence/public-math-benchmarks.json)

Codex then reviewed the same checkpoint on the other four known development problems. All three truck optimization responses ended naturally and gave decimal values for the requested exact middle speed. The Gaokao cube response reached the 6,144-token limit without a visible answer. All four failed the full-prompt review, bringing the combined result to **8 complete solutions out of 12**. [Supplemental generation and review receipts](../evidence/public-math-benchmarks.json)

The checkpoint tied the accepted parent on the same 370 MMLU items: **226/370 (61.1%)**, with 162/270 in high school and 64/100 in college. One high-school answer became correct and one became incorrect; every college choice matched. This pilot recovered more known worked cases while holding overall MMLU accuracy. It remains experimental. [Paired benchmark receipts](../evidence/public-math-benchmarks.json)

## Fifth repair pilot: build from an experimental checkpoint

The fifth pilot starts from the third pilot on a separate branch, where the three calculus responses and the cube proof had already stopped looping but still lacked correct exact results or complete working. Five reviewed continuations target the exact calculus results and the two incomplete Gaokao proofs. The edit keeps 15,975 recorded states in its guard projection, including full recorded native prefixes for the calculus and inequality repairs.

All 283 target tokens won the rounded full-vocabulary CUDA check, with no omitted targets. The D63 edit has norm 102.09% of its experimental parent's D63 norm. The new GGUF was independently verified, with byte equality outside D63. This unusually large edit is an experiment; fixed-state success alone does not qualify it. [Fit and saved checkpoint receipts](../evidence/public-math-benchmarks.json)

In ordinary generation, all three calculus variants produced their independently verified exact optima and derivative arguments at 647, 645, and 629 tokens. The inequality also produced its complete rigorous proof. Both algebra cases, the differential equation, and exact Bayes passed, for **8 complete solutions out of 12 known cases**. All twelve ended naturally, and both critical proofs matched exactly. The cube response again gave 6/35 but omitted the exhaustion proof. All three statistics answers gave exact formulas in the working and then rounded their final entries, so this pilot failed the required precision. [Ordinary generation and review receipts](../evidence/public-math-benchmarks.json)

Matched MMLU scored **224/370 (60.5%)**, down two from the accepted parent. High school was 160/270 and college was 64/100. Two high-school items became correct and four became incorrect. The experiment recovered all three calculus solutions while losing exact statistics precision and some broader score, so it was not selected for the fresh comparison. [Paired benchmark receipts](../evidence/public-math-benchmarks.json)

## Fresh worked comparison plan

The fresh comparison is separate from the development repairs and the repeated MMLU comparison. Its twelve authored questions, five high-school and seven college, and their grader-only answer key were frozen before the repair candidates were selected. The prompts and key are private while the comparison is pending.

The fourth pilot is the default candidate. The fifth would replace it for this comparison only if it retains all eight reviewed solutions, repairs at least one additional calculus or cube case, preserves both critical proofs exactly, and scores at least 226/370 on matched MMLU. Codex will freeze both models' ordinary outputs, grade complete visible working with randomized model labels, and then reveal the labels. No fresh question, answer key, or result is an input to these fits. [Frozen evaluation and selection commitments](../evidence/public-math-benchmarks.json)

The fourth pilot was selected before fresh generation because the fifth did not retain the required statistics precision. [Frozen launch receipt](../evidence/public-math-benchmarks.json)

All 24 responses were frozen before the answer key was opened. Codex graded the visible working with randomized model labels and froze the grades before unblinding.

| Fresh measure | Accepted rank-two | Fourth pilot |
| --- | ---: | ---: |
| Complete correct work, high school | 3/5 | 4/5 |
| Complete correct work, college | 5/7 | 6/7 |
| Complete correct work, overall | 8/12 | 10/12 |
| Correct final result | 9/12 | 11/12 |
| Natural endings | 10/12 | 12/12 |

The edit gained two complete solutions and lost none: an exact constrained optimization and a complex-residue calculation. The optimization gain applies the stated strict rubric to an inconsistent displayed cost equality; overlooking that equality as a typo would change the overall comparison to 9/12 versus 10/12. The geometry probability was correct in the edited answer, but its count lacked a proof of exhaustiveness. Both models used the correct Bayes setup and made an arithmetic error when simplifying one posterior.

On the eight matched problems that both solved completely, median output increased from 999 to 1,413 tokens and median decoding time increased from 22.97 to 33.31 seconds. The exact statistics problem was faster for the edit, 64.08 seconds versus 103.14, and both answers were complete. These are results on a small fresh set; they show a gain in complete solutions and completion with a speed tradeoff. [Frozen generation, blind grades, and paired aggregate](../evidence/public-math-benchmarks.json)

An independent replay of the saved fourth checkpoint preserved all 10,843 archived token winners and the corresponding upstream activation bytes. Both prior Euler decision margins reproduced exactly. This qualifies that archive and the two ordinary proof controls; it does not establish behavior outside the measured cases. [Archived replay receipt](../evidence/public-math-benchmarks.json)

## Pilot 026 accuracy diagnosis

The diagnostic drew 24 of Pilot 024's 144 immediate-choice misses and eight previously correct controls. Sampling covered both math splits and a range of answer-score margins. Codex solved all 32 independently before comparison with the official key. Every independently derived choice agreed with the key. [Sampling and answer verification](../evidence/mmlu-accuracy-diagnostic-026.json)

With a prompt asking for justified work, Pilot 024 chose correctly on **23 of the 24 sampled misses**. Independent review found **20 complete correct solutions**, two correct choices with proof gaps, one correct choice despite a numerical error, and one response that ended at the cap without a visible answer. All eight controls gave complete correct work. This comparison changes the prompt and allows generation, so it measures recovery under that protocol on the sampled problems. [Worked diagnostic receipts](../evidence/mmlu-accuracy-diagnostic-026.json)

In a separate immediate-choice test, all 32 original-order prompts and all 128 associated logits matched the archived benchmark. Three cyclic option rotations kept the question and five demonstrations fixed. **16 of 24** sampled misses became correct in at least one rotation. **Four of eight** previously correct controls became wrong in at least one rotation. The model chose the same answer content in all four orders on 11 of the 32 items. This shows that option order contributed to the scored outcome in this sample. [Rotation protocol and receipts](../evidence/mmlu-accuracy-diagnostic-026.json)

An evaluation-only CUDA capture recorded all **128 terminal states** and reproduced all **512 archived choice logits** bit for bit. For each rotated prompt, we crossed the two terminal states with the two answer-to-output-row assignments. Averaging both swap orders separated the change in the correct answer's margin over the original winner into a terminal-state term and a row-assignment term. Over the 72 changed-order trials on prior misses, the mean margin increased by **1.363 logits**. The terminal-state term contributed **0.330** and the row-assignment term **1.033**. All 96 pairwise comparisons reconciled exactly. [Activation and margin receipts](../evidence/mmlu-accuracy-diagnostic-026-activation.json)

Of the 31 observed recoveries, 11 also recovered when changing the assignment alone at the original state. The other 20 required both changes in the tested score table. A fixed-state reassignment keeps the winning displayed letter fixed, so the cyclic design mechanically produces one assignment-only recovery per previously missed item. The overlap with observed recoveries and the paired margin terms describe the readout behavior on this sample. The capture measures terminal states across four cyclic orders, leaving upstream circuit attribution and population prevalence unmeasured. All diagnostic inputs and activations remain outside fitting. [Counterfactual and scope details](../evidence/mmlu-accuracy-diagnostic-026-activation.json)

The subsequent direct D63 edit corrected two authored rotations and preserved every other authored choice. On the matched MMLU set, it scored **222/370 versus 226/370** and lost four previously correct high-school items without gaining any. Both exact proof checks also failed, so the independently authored fresh set stayed sealed. [Pilot 026 evidence and replay](case-study.md#twenty-sixth-pilot-with-option-order-repairs)

The two-row Pilot 027 edit improved one previous miss and lost two previous correct answers on the same matched suite, for **225/370 versus 226/370**. It preserved both exact proofs and the correct 282-token cylinder solution. The net accuracy gate failed. [Pilot 027 evidence and replay](case-study.md#twenty-seventh-pilot-with-two-packed-answer-rows)

Pilot 028’s grouped authored tests improved both pooled measures, but matched MMLU stayed at **226/370** with ten gains and ten losses. It preserved the interval proof and the 282-token cylinder. The correct Euler answer used a different token stream and failed exact replay. [Pilot 028 evidence and replay](case-study.md#twenty-eighth-pilot-with-held-family-training)

## Pilot 176 matched and blinded results

The saved four-row scale edit improved from **226/370 to 228/370** on the matched MMLU suite. It recovered two high-school answers and retained all 226 previous correct answers. Both protected proof streams and the correct natural **282-token** cylinder completion matched exactly. [Matched score](../evidence/direct-accuracy-pilot-179-provisional-matched-scale.json) · [Protected generation](../evidence/direct-accuracy-pilot-178-provisional-protected-generation.json)

The separate blinded run tied at **42/96** correct trials and **2/24** problems correct in all four answer orders, with no gains or losses. The candidate therefore missed the fresh skill requirement. [Blinded evaluation](../evidence/direct-accuracy-pilot-180-blinded-fresh-scale.json)

## Pilot 194 mixed packed edit

Pilot 194 changes 158 binary16 scale fields and 21 four-bit codes in four answer output rows. The saved GGUF reproduced both protected proof streams exactly and naturally finished the cylinder in **282 tokens**, with the same visible solution as Pilot 024. Observed CUDA decode time for the cylinder was **6.04 seconds** versus **6.46 seconds** for the reference. This timing is for one protected case. [Exact protected replay](../evidence/direct-accuracy-pilot-195-protected-mixed-output.json) · [Saved-file readback](../evidence/direct-accuracy-pilots-194-198-mixed-output.json)

The same saved file scored **229/370 (61.9%)**, up from **226/370 (61.1%)**, on the exact matched MMLU suite. High school improved from 162/270 to 165/270. College remained at 64/100. All 226 previously correct items stayed correct. The comparator verified identical ordered prompts and native settings. The saved checkpoint passed both prerequisites before the separate P181 evaluation was prepared. [Matched results and qualification hashes](../evidence/direct-accuracy-pilot-195-matched-mixed-output.json)

The blinded P181 comparison used 24 independently checked problems in four answer orders each. Both anonymous 96-trial outputs were frozen before grading. Pilot 194 improved from **45/96 to 47/96** with two gains and zero losses. Both checkpoints solved **4/24** problems in every order, and the number of problems with the same answer content in all four orders fell from seven to six. The predeclared gate required gains in both total correct trials and problems correct in every order. Pilot 194 remains provisional. [Blinded aggregate and frozen receipt hashes](../evidence/direct-accuracy-pilot-194-p181-blinded-fresh.json)

Pilot 209 passed archived-state fitting with two more complete condition pairs and zero previous authored choice losses. The saved file reproduced **one of the two** protected proofs. The live gate stopped at that failure before the cylinder, matched, or blind evaluation. [Packed fit and measured limits](case-study.md#pilot-209-with-two-additional-complete-condition-pairs) · [Exact protected gate](../evidence/direct-accuracy-pilot-213-protected-rejection.json)

Pilot 217 kept those authored gains and reduced the peak ordinary logit movement to **0.02091** in the archived proxy. Its saved checkpoint still reproduced **one of the two** protected proofs exactly. Qualification ended before matched or final-blind evaluation. [Fit and relative drift measurements](case-study.md#pilots-216-and-217-with-the-original-ordinary-logit-limit) · [Protected rejection](../evidence/direct-accuracy-pilot-218-protected-rejection.json)

## Pilot 241 with six-bit group minima

Pilot 241 was fit on authored development states and saved as an exact four-row packed edit. It reproduced **both** protected proof streams and the correct natural **282-token** cylinder completion. Observed CUDA decode time was **6.11 seconds** versus **6.46 seconds** on that cylinder case. [Fit and saved-model replay](case-study.md#pilot-241-with-exact-subgroup-minimum-edits) · [Protected evidence](../evidence/direct-accuracy-pilot-241-grouped-output.json)

On the same 370 matched MMLU questions, Pilot 241 scored **230/370 (62.2%)**, up from **226/370 (61.1%)**. High school improved from **162/270 to 166/270** and college stayed at **64/100**. The comparator verified four gains and zero losses among the 226 prior correct answers. The checkpoint qualified for the separate final-blind test. [Matched receipts and source-pinned qualification](../evidence/direct-accuracy-pilot-241-grouped-output.json)

The separate P204 test froze two anonymous outputs for 32 independently checked problems in four answer orders. Pilot 024 and Pilot 241 each answered **65/128** trials correctly and solved **8/32** problems in all four orders. The predeclared gate required gains on both measures. Pilot 241 remains provisional, and further candidates require a fresh blind set. [Blinded aggregate and custody receipts](../evidence/direct-accuracy-pilot-241-grouped-output.json)
