# Optional future method: joint teacher-span SOC formulation

**Status: formulation and 13 synthetic diagnostic groups only. No joint optimizer, native execution, model fit or mathematical-answer improvement is established.** This is an optional future direction. It changes no active model experiment, accepted checkpoint or gate. The separate [native gradient probe](../sequence-gradient-probe/README.md) remains **UNRUN_NATIVE**.

One desired next token can have a valid local margin without producing a complete correct continuation. This formulation asks how several teacher-forced transitions could share **one saved matrix update**, with coupled preservation and norm constraints. It is supervised fitting to selected training states, not evidence of autonomous learning or a new model-editing result.

## Start with the actual corrected prefixes

Validate a complete mathematically correct teacher response, its tokenizer/template and whole-message tokenization. Locate the first actual token divergence and the required span; one visible symbol need not correspond to one token. Capture each selected state's features on its **corrected teacher prefix**. Archived activations after an earlier changed token belong to a different prefix.

Keep data roles explicit. Features placed in guard constraints or used to choose the basis are fitting exposure. Evaluation-only cases must not silently enter the optimizer, guard matrix or nullspace. No private questions, teacher bodies, model activations or weights are included here.

For the verified terminal-down architecture, fixed-prefix features can be reused only if the selected matrix has no path into upstream cached/recurrent state, and all other relevant weights, backend operations, precision and state handling remain fixed. Being after the last KV write is not a universal proof. Establish the dependencies and calibrate them in the actual runtime; this package provides no new native identity evidence.

**Selected-token constraints do not guarantee greedy reachability of later selected prefixes.** Cover and verify every intervening decision through the span, or label the result teacher-forced diagnostics and require ordinary generation. After an unverified divergence, an old cached trajectory does not describe the candidate's new branch.

## The fixed-feature, fixed-head idealization

Let the edited down matrix have mathematical shape $D\in\mathbb R^{d\times n}$. Put supplied guard inputs in the rows of $G$. Choose a **fixed** basis $K\in\mathbb R^{n\times k}$ with $GK=0$, and make only $U\in\mathbb R^{d\times k}$ variable:

$$
\Delta D=UK^\top,\qquad q_i=K^\top a_i,\qquad s_i=r_i+Uq_i.
$$

Here $a_i$ and $r_i$ are the frozen control input and residual on corrected prefix $i$. This is a real-arithmetic proposal. It does not assert equality with an edited native F32 matrix multiplication.

For a **fixed bias-free decoded head**, fixed RMS gain $\gamma$, fixed $\epsilon>0$, desired row $w_{y_i}$ and competitor row $w_c$, define

$$
t_{ic}=\gamma\odot(w_{y_i}-w_c),\qquad
z_{y_i}-z_c=\frac{t_{ic}^\top s_i}{\sqrt{\|s_i\|_2^2/d+\epsilon}}.
$$

For a fixed positive required margin $m_{ic}>0$, the ideal constraint is equivalent to

$$
\left\|\begin{bmatrix}s_i/\sqrt d\\\sqrt\epsilon\end{bmatrix}\right\|_2
\le \frac{t_{ic}^\top s_i}{m_{ic}}.
$$

This is a norm of an affine function bounded by an affine function of $U$: the standard affine second-order cone form in the [CVXPY authors' SOCP documentation](https://www.cvxpy.org/examples/basic/socp.html). CVXPY is a reference here, **not a dependency**. The cone requires a nonnegative right side. Its $\sqrt\epsilon$ coordinate is a fixed constant, not an extra variable that may move to make a fit easier.

For zero margin the condition becomes the linear inequality $t_{ic}^\top s_i\ge0$. This convexity argument does not cover negative required margins. It also does not cover jointly learning $K$, changing the head or features, or assuming quantized/native arithmetic follows the decoded-linear formula.

Cauchy–Schwarz gives the necessary finite-feasibility condition $\sqrt d\|t_{ic}\|_2>m_{ic}$ when $\epsilon>0$. This is not sufficient for the coupled problem or its caps. A near-threshold floating-point comparison is not a rigorous infeasibility certificate.

## One coupled matrix objective and fixed-reference caps

The intended minimum-energy objective is

$$
\frac12\|UK^\top\|_F^2
=\frac12\operatorname{tr}\!\left(U(K^\top K)U^\top\right).
$$

For orthonormal columns of $K$ this becomes $\tfrac12\|U\|_F^2$, a strictly convex objective. With nonorthonormal columns, dropping the Gram matrix $K^\top K$ changes the objective. Rank-revealing orthonormalization must transform the keys/factors consistently; do not hide a ridge or invert a nearly singular Gram matrix. A small chosen basis defines a restricted subproblem, not an optimum over every possible model edit.

Fixed limits such as $\|UK^\top\|_F\le B$ and $\|Uq_i\|_2\le\rho_i$ are convex. To bound cumulative drift from a preserved reference, freeze a common numeric representation and let $H=D_C-D_A$:

$$
\|H+UK^\top\|_F\le B_{\rm total},
$$

$$
\|H+UK^\top\|_F^2
=\|H\|_F^2+2\langle HK,U\rangle
+\operatorname{tr}\!\left(U(K^\top K)U^\top\right).
$$

Pin the exact decoding/representation of a quantized reference before computing these constants. Their terms can be accumulated in bounded streams. A cap normalized by a changing candidate norm is not the fixed convex cap above.

All states share the same $U$. Independently repairing residuals and summing their matrix updates does not solve this coupled problem. Zero keys cannot move their states. Identical keys can be compatible, while identical residual/key pairs with opposing positive-margin requirements are contradictory. Nearly dependent keys may demand large matrix energy. These observations concern the fixed basis and contract, not global impossibility of improving a model.

## What remains before an actual edit

No joint solver is implemented in this package. A future solver must use the correct common metric and fixed epsilon slice. For orthonormal $K$ and $q_i\ne0$, a residual-space projection $s_i^*$ lifts to

$$
U_{\rm new}=U+(s_i^*-s_i)q_i^\top/\|q_i\|_2^2.
$$

That identity alone is not a joint optimization algorithm. A Dykstra design would need retained corrections in the common metric; ordinary cycling is not minimum-energy projection. Numerical residuals or dual gaps without rigorous error bounds are diagnostics, not exact certificates.

A future active-competitor loop must scan the full vocabulary at **every** selected state, add actual violating competitors and solve within a frozen budget. A small shortlist is insufficient. Any ideal optimum certificate would apply only to the same fixed real-arithmetic subproblem. Native arithmetic mismatch, repeated violations or stalled iterations remain unresolved conditions.

Materialize a separate direct F32 checkpoint in bounded chunks. Re-read it and compute the actual stored update, incremental/cumulative Frobenius norms, supplied guard responses and all positive residual caps. Intended nullity can disappear after rounding. Then require native full-vocabulary margins, earlier-prefix preservation, ordinary complete answers, valid displayed mathematics, termination, format and regressions. Use fresh runtime state unless cache independence has actually been established. These gates remain necessary even if an ideal proposal is feasible.

## Inspect or run the tiny diagnostic

The [NumPy source](joint-teacher-span-soc-future-v1.py) uses invented arrays only. With the repository's existing Python 3.11+ and NumPy environment, run from the repository root:

```sh
python prototypes/joint-teacher-span-soc/joint-teacher-span-soc-future-v1.py
```

It prints a compact status. Optional `--receipt NEW_FILE.json` writes a new receipt and refuses to overwrite one. The functions support the script's bounded fixtures; they are not a validated general optimizer API. The frozen receipt used Python 3.13.7 and NumPy 2.2.1; this byte-exact public copy does not constitute a new cross-platform execution check.

The [frozen receipt](joint-teacher-span-soc-future-v1.verification.json) records 13 passing groups: SOC/margin identities; finite Jensen checks; two directional gradients; the affine adjoint; orthonormal and weighted metrics; cumulative drift; feasible joint and duplicate-key cases; a toy opposed-margin contradiction; zero keys; near-collinear interpolation stress; and F32 guard leakage. In the rounding example, intended guard response zero becomes stored response `1.1920928955078125e-7`. This is a synthetic counterexample, not a measurement of any model candidate.

Finite Jensen or finite-difference checks do not prove convexity, real-edit feasibility, global optimality, native equivalence or model quality. No diagnostic tests were rerun for this public copy: its source and receipt remain byte-exact, with source SHA-256 `5ed9b2cbe94b72a6a10cce5faad0c15a98d913167c2ae09286f42f2abaffea93`.

## Provenance and license

This README is a curated public derivative of a private formulation; the [source-audit summary](independent-review.json) is also a labeled derivative. The [distribution manifest](freeze.json) records their new hashes, byte-exact diagnostic/receipt hashes and original private provenance hashes. Original private design/audit/freeze bytes are not distributed or misidentified as the public derivatives.

The original project diagnostic and documentation use the repository's [MIT license](../../LICENSE). No CVXPY code, solver, model weights, native library, teacher text or private evaluation data is bundled. This formulation is an engineering construction using standard convex optimization; no novelty or generalized learning/speed claim is made.
