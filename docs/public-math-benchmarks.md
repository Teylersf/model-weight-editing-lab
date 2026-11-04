# Public math benchmarks

We froze the saved Windows rank-two checkpoint before running these public evaluations. E10 is the preceding accepted research checkpoint. The Huihui GGUF is the vendor checkpoint from before the lab's edits. Their file hashes identify the exact models used locally. [Windows qualification and checkpoint hashes](../evidence/experiment-summary.json)

## MMLU answer selection

We use the entire `high_school_mathematics` and `college_mathematics` test splits, with 270 and 100 questions respectively. Each raw prompt uses the five official development examples for its subject and ends with `Answer:`. We take the highest next-token logit among the four leading-space answer tokens. The original evaluator used a legacy completion API with a top-100 fallback. This run observes all four logits directly and uses no generated explanation. [Original data and evaluator](https://github.com/hendrycks/test/tree/4450500f923c49f1fb1dd3d99108a0bd9717b660)

The test denominator includes every question. Invalid and censored cases are reported separately and count as incorrect. Combined accuracy gives equal weight to every question. A paired comparison reports questions each checkpoint uniquely got right, so equal totals can still show changes. These public splits may overlap the upstream model's training data. Scores describe these benchmark questions, with no conversion to school grades or student percentiles.

| Full test split | E10 | Windows rank-two |
| --- | ---: | ---: |
| High school mathematics | 160 / 270 (59.3%) | 162 / 270 (60.0%) |
| College mathematics | 64 / 100 (64.0%) | 64 / 100 (64.0%) |
| Combined | 224 / 370 (60.5%) | 226 / 370 (61.1%) |

Both checkpoints produced valid logits on all 370 questions, with zero prompt limit hits and zero ties. Rank-two corrected two high-school answers. The other 368 answer choices were identical, including all 100 college answers. The published preparation and grading script reproduced both scores against the archived CUDA outputs. [Scoring source and rerun commands](../prototypes/windows-cuda-mmlu-math/README.md) · [Aggregate receipt](../evidence/public-math-benchmarks.json)

## Worked solutions

The school sample uses 16 text questions from the released AGIEval exam corpus. It contains eight SAT Math multiple-choice questions, four Gaokao math multiple-choice questions, and four Gaokao math fill-in questions. [AGIEval v1.1 release](https://github.com/ruixiangcui/AGIEval/tree/84ab72d94318290aad2e4ec820d535a95a1f7552/data/v1_1)

The college sample uses one open-response stem in each of eight UGMathBench subjects, with all three randomized variants for each stem. We report both variant-level performance and the number of stems whose three variants all pass. Variants from the same stem are related, and this diagnostic uses only eight stems. [UGMathBench paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/c3af3531df85264decc31382cb319781-Abstract-Conference.html) · [Pinned release](https://huggingface.co/datasets/UGMathBench/ugmathbench/tree/8ab16f0c131a9b3b52195e64175cb5a8f3881bbf)

Worked runs use the same inputs and inference settings across checkpoints. The grading tracks the final result, valid and complete visible working, natural completion, and repeated work separately. Token counts and decode time are compared among correct, complete solutions. The small, text-only samples cover specific exam and coursework tasks. They leave coverage of images, wider curricula, and student interactions to separate evaluation.
