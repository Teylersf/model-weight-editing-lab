# Local math method library

This is a self-hosted math reference for a tutor. Search an equation or a short description of the task. Each result gives the method, its assumptions, steps, common mistakes, checks, and an original worked example. The library contains 275 English-language cards across 21 subjects, with 103 high-school and 172 undergraduate methods.

## Run the library

Use Node.js 22.13 or newer. Run these commands from this directory.

```text
node math-methods/cli.mjs build
node math-methods/cli.mjs search "I squared both sides of sqrt(w+5)=w-1. How do I check the candidates?"
node math-methods/cli.mjs resolve "Law of cosines"
node math-methods/cli.mjs show radical-equations
node math-methods/cli.mjs coverage
node --test math-methods/library.test.mjs
```

The build validates card fields and unique IDs before replacing the local SQLite snapshot in `.runtime/math-methods.sqlite`. The database uses the SQLite full-text index bundled with Node. Search is read-only and needs no network, model, or GPU. [SQLite FTS5](https://www.sqlite.org/fts5.html) · [Node.js 22 SQLite API](https://nodejs.org/download/release/v22.19.0/docs/api/sqlite.html)

## Use it as a tool

Import `openMethodLibrary()` from `math-methods/library.mjs`. Use `search({ query, domain, level, limit })` to retrieve ranked candidates for a problem. The default result limit is three, with a maximum of eight. Use `resolve({ name, domain, level })` when the caller can name a method. It matches a complete title or alias and returns one card or `null` for an unknown or shared name. `get(id)` loads one card by its stable ID.

The optional `domain` is a subject slug from the coverage command. The optional `level` is `high-school` or `undergraduate`. Call `close()` after using the library. Record `revision` and `searchRevision` when comparing runs. The StepMargin beta exposes local HTTP routes for these operations. Use `POST /api/math-methods/search` with `{ "query": "…" }`, `POST /api/math-methods/resolve` with `{ "name": "…" }`, or `GET /api/math-methods/cards/:id` for a stable card ID. Search can return an empty list, resolve can return `null`, and an unknown card ID returns HTTP 404 with `method: null`. Each lookup response includes both revisions.

The method is a candidate procedure. Check its assumptions against the submitted problem before applying it. Calculator or symbolic verification of the student's particular inputs is a separate operation. For a drawing or screenshot, a future tool caller supplies the relevant text or notation it read from the picture.

## Measured coverage and limitations

The included tests find an expected card in the top three for all 89 development queries, with 85 ranked first. The five included off-topic controls return no cards. The search recognizes selected notation and intent cues, including bare equation systems, rational inequalities, and compass bearings. It uses the same SQLite index for fallback search.

A prior audit froze 24 math requests and 10 controls before searching. The old ranking matched an expected card first on 9/24 and in the top three on 17/24. It returned no cards for 3/10 controls. The audit was used as development input for the updated ranking.

A separately authored audit froze 32 new math requests and 12 controls before running either implementation. Both runs received identical text without filters and returned up to three cards per query. This comparison used the 257-card snapshot.

| Measure | Prior ranking | Updated ranking |
| --- | ---: | ---: |
| Expected method first | 17/32 | 18/32 |
| Expected method in top three | 23/32 | 22/32 |
| No cards for off-topic controls | 1/8 | 1/8 |
| No cards for underspecified controls | 0/4 | 1/4 |

Five card clarifications cover quadrant bearings, paired t intervals, change-of-variables Jacobians, vector line integrals, and KKT assumptions. A controlled run using the original database for both rankings produced the same aggregate scores. The library is available for manual reference. Automatic tutor lookup is gated on ranking and abstention.

The updated ranking audit used card revision `4c94348ec614a1e205f252afa8811c5b8c93ad7025f97e2609501d8461d3d551` and search revision `a26fa4b7154a9122478c003799779c10ebbc38f21a257870b0519005fadd36f1`. The original audit bundle SHA-256 was `2f1d0759b1cca9ba24da8135c7df8631380de7086801cf2cabf6e90ceff54053`. The fresh audit manifest SHA-256 is `4852a4c3e2196e832ae4bd16543272600b5e19f8c9e5accf74ea8e8b3198091c` and the aggregate comparison receipt SHA-256 is `fe50b8e6a88b1334b10fbd8d3b01a44df6689dfc4846b2c97769faed21f11804`.

A second independent audit of the 257-card library found the expected card first on 14/18 strongly matchable questions and in the top three on 17/18. It returned an empty list on 2/6 underspecified and 3/6 nonmath questions. The queries and key were sealed before retrieval. The manifest SHA-256 is `cbe764f3f11d54809d8807453fb710931e773ec28cebd73b64239f3f016d1fdd` and the aggregate receipt SHA-256 is `a5b123f5e2566b7f4ef09fa6f4fd5a1217495399306899db626778f870d1344b`. These results measure free-text search. The named resolver has a separate input contract.

The 263-card expansion adds logarithmic inequalities, study design, one-way ANOVA, local ODE existence and uniqueness, the fixed-end heat equation, and Cauchy’s integral formula. A replay of the second audit on that snapshot preserved all four aggregate counts, with 29 of 30 ranked lists identical. The named resolver returned the expected card for all 1,176 unique titles and aliases after normalization and returned no card for all four shared labels without filters. That card revision was `61d16ceb0b225ada698d462987197d92dd6106bb49f32ea91c1962e10e70a789`. The replay receipt SHA-256 is `2c56d60972f6e6838b2aaf17e5157971b7a7cd552126ad8ac83876279f3b40c5`.

The 275-card snapshot adds twelve original procedures, including probability trees, infinite geometric series, proof by contradiction, trigonometric integrals, Markov-chain absorption, and QR least squares. All 66 new titles and aliases resolve without scope filters. Replaying the same audit with the same search implementation preserved the aggregate counts, with 25 of 30 ranked lists identical to the 263-card snapshot. This was a regression check on a previously evaluated set. The current card revision is `e3209e6bd7a38aef98859092d3c778f837e57a3ab5e20eab1526890ecdde8668`, and the lookup revision is `e95428c1ff44da06cc384e77dc03793e3a2a224e90a34a0b4cf00656e5ef38bb`.

The JSON files in `math-methods/cards` are the editable source. Their examples are authored for this library. Keep model benchmarks, held-out evaluation items, and student submissions separate from the library.
