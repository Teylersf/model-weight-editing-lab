# Direct weight-editing methods for the Qwen lab

5 November 2026

The lab edits stored weights and verifies the saved checkpoint on the intended CUDA runtime. That workflow has established a narrow result. Pilot 016 preserved all 370 matched MMLU choices and all 1,480 answer logits while cutting the cylinder solution from 486 to 282 tokens. Its Euler solution was incorrect. Pilot 020 kept the cylinder speedup and replayed Euler exactly, but its interval proof reached the token cap without a visible answer. These experiments show why the proof and free-response checks are essential even when fixed-prefix logits match. [Pilot 016 evidence](../evidence/direct-closure-pilot-016.json) · [Pilot 020 evidence](../evidence/direct-closure-pilot-020.json)

## Related implementations

| Method | What transfers to this project |
| --- | --- |
| Astra’s weight-space programming experiment | The authors traced repeated reasoning in Qwen3.5-0.8B to an internal direction and removed that direction from selected MLP output columns in two layers. They reported MATH-500 moving from 7.9% to 48.1% with their sampling settings, and the token-cap rate fell from 93% to 33.1%. Their smaller Gemma experiment did not establish a math improvement. We can reuse the trace-and-intervene workflow and discover the relevant direction on our checkpoint. [Experiment and protocol](https://rikiyat.github.io/blog/weight-space-programming/#experiment-8) · [GitHub logs](https://github.com/RikiyaT/lm_understand-logs) |
| Steer2Edit | Contrast activation traces, rank relevant attention or MLP components, and convert the direction into persistent rank-one edits. The reasoning experiment reported shorter traces at comparable aggregate accuracy on Qwen3-4B-Thinking and OpenMath-Nemotron-7B. It found evidence for distributed MLP involvement in those models. Use the ranking procedure to select candidates on our own model. [GitHub](https://github.com/Trustworthy-ML-Lab/Steer2Edit) · [Reasoning experiment](https://arxiv.org/html/2602.09870v3#S4.SS1.SSS3) |
| AlphaEdit and EMMET | AlphaEdit projects the update away from represented preservation activations. EMMET solves multiple target constraints together. We can reuse the projection and batch the candidate solve. The published projects target knowledge editing, and AlphaEdit lists a 48 GB GPU for its setup. The algebra can guide a separate CPU implementation for this GGUF workflow. [AlphaEdit](https://github.com/jianghoucheng/AlphaEdit) · [EMMET code](https://github.com/scalable-model-editing/unified-model-editing) |
| AnyEdit | It splits long outputs into chunks and edits selected token decisions across the sequence. That is a useful analogy for calculator workflows that require several dependent decisions. Its published evaluations measure long-form knowledge editing, and its reference setup lists an 80 GB GPU. [GitHub](https://github.com/jianghoucheng/AnyEdit) · [ICML paper](https://proceedings.mlr.press/v267/jiang25b.html) |

## Where to shorten the loop

The saved row patches are small, but the packed search can require repeated integer fits and each materialized checkpoint is 11.67 GB. The Pilot 016 MMLU scoring phase took 239 seconds from the first scored prompt to the last. Reuse the development captures across candidate fits and reserve full generation, checkpoint readback, and public benchmark runs for a shortlist.

For calculator use, build matched development traces for a necessary follow-up, a repeated calculation, and a ready-to-report checked result. The Newton trace illustrates the distinction. After the second update, a residual check is still necessary, so the edit should affect which expression is requested at that step. When all requested calculations are complete, a separate trace can test whether the model begins the visible answer.

Rank a few components using interventions on those contrasts. Fit low-rank candidates with a cached preservation projection or regularized system, then test the exact rounded candidate weights in a batched native replay. Start with the existing floating-point terminal feed-forward instrumentation, and add earlier layer captures when the contrast points there. Save a full GGUF only after the native screen. Preserve the earlier proof gates and use a fresh set to measure correct completion, necessary dependent calls, redundant calculations, and latency together.

These sources establish useful methods and tradeoffs on their reported tasks. A speedup in finding a qualified edit on this quantized 27B checkpoint remains a local measurement.
