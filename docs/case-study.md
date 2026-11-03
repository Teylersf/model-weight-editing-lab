# Case study: direct saved-weight edits of Qwen3.8-27B Abliterated

**Research snapshot: 2026-11-03. Project lead: Taylor Kalin.** OpenAI Codex and AI assistants helped develop tooling, check mathematics, and write documentation. The results below distinguish recorded behavior from demonstrated mathematical improvement.

These experiments changed actual saved GGUF weights of **Qwen3.8-27B Abliterated**. The local snapshot was `Huihui-Qwen3.8-27B-abliterated-UD-DW-IQ3_XXS.gguf`, from the [publisher's pinned GGUF repository](https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF/tree/1c69098e9c32db6dc06fc48f1d6cc75ad07da89e). Its verified original SHA-256 was `bfc6892863eceb16f69697e59b038acdc1c709b790c1542e4612dbb0924d3568`. This identifies the specific lab artifact; other conversions and revisions can differ.

The aim was faster, decisive school and university mathematics with correct complete solutions. The base remained immutable while separate candidate files were evaluated. There is no accepted “best mathematics model” result in this snapshot.

## Reading the evidence

**B** denotes the original baseline. **P** is the frozen V5 candidate used as the parent for V6/V7. **C** denotes a no-edit representation or packing control where needed; **E** denotes an edited candidate. A changed file, a successful numerical fit, a passed saved-prefix check, and an improved complete answer are four different observations.

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

## V8: internal weight editing remains in progress

V8 is investigating a small update to an internal terminal feed-forward down projection, alongside complete correct mathematical training continuations and counterbalanced examples where coefficients such as `6` are valid. The goal is to improve a coherent solution, rather than merely favor one digit or close thinking sooner.

The historical local `terminal-down-stream-v8-verification.json`, which is not bundled here, is explicitly synthetic. It checks streamed F32 materialization and numerical responses, including a case where rounding breaks an intended zero response. Native captures, representation controls, full-prefix behavior, and complete mathematical outputs remain work in progress. No accepted V8 model result is asserted here.

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
