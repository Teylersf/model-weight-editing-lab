# Local math method library

This is a self-hosted math reference for a tutor. Search an equation or a short description of the task. Each result gives the method, its assumptions, steps, common mistakes, checks, and an original worked example. The library contains 257 English-language cards across 21 subjects, with 95 high-school and 162 undergraduate methods.

## Run the library

Use Node.js 22.13 or newer. Run these commands from this directory.

```text
node math-methods/cli.mjs build
node math-methods/cli.mjs search "I squared both sides of sqrt(w+5)=w-1. How do I check the candidates?"
node math-methods/cli.mjs show radical-equations
node math-methods/cli.mjs coverage
node --test math-methods/library.test.mjs
```

The build validates card fields and unique IDs before replacing the local SQLite snapshot in `.runtime/math-methods.sqlite`. The database uses the SQLite full-text index bundled with Node. Search is read-only and needs no network, model, or GPU. [SQLite FTS5](https://www.sqlite.org/fts5.html) · [Node.js 22 SQLite API](https://nodejs.org/download/release/v22.19.0/docs/api/sqlite.html)

## Use it as a tool

Import `openMethodLibrary()` from `math-methods/library.mjs` and call `search({ query, domain, level, limit })`. The optional `domain` is a subject slug from the coverage command. The optional `level` is `high-school` or `undergraduate`. The default result limit is three, with a maximum of eight. `get(id)` loads one card by its stable ID. Call `close()` after using the library. Record `revision` and `searchRevision` when comparing runs.

The method is a candidate procedure. Check its assumptions against the submitted problem before applying it. Calculator or symbolic verification of the student's particular inputs is a separate operation. For a drawing or screenshot, a future tool caller supplies the relevant text or notation it read from the picture.

## Measured coverage and limitations

The included tests find an expected card in the top three for all 77 development queries, with 75 ranked first. The included off-topic controls return no cards. The search recognizes selected notation and intent cues, including bare equation systems, rational inequalities, and compass bearings. It uses the same SQLite index for fallback search.

A prior audit froze 24 math requests and 10 controls before searching. The old ranking matched an expected card first on 9/24 and in the top three on 17/24. It returned no cards for 3/10 controls. The audit was used as development input for the updated ranking.

A separately authored audit froze 32 new math requests and 12 controls before running either implementation. Both runs received identical text without filters and returned up to three cards per query.

| Measure | Prior snapshot | Current snapshot |
| --- | ---: | ---: |
| Expected method first | 17/32 | 18/32 |
| Expected method in top three | 23/32 | 22/32 |
| No cards for off-topic controls | 1/8 | 1/8 |
| No cards for underspecified controls | 0/4 | 1/4 |

Five card clarifications cover quadrant bearings, paired t intervals, change-of-variables Jacobians, vector line integrals, and KKT assumptions. A controlled run using the original database for both rankings produced the same aggregate scores. The library is available for manual reference. Automatic tutor lookup is gated on ranking and abstention.

The current card revision is `4c94348ec614a1e205f252afa8811c5b8c93ad7025f97e2609501d8461d3d551` and the search revision is `a26fa4b7154a9122478c003799779c10ebbc38f21a257870b0519005fadd36f1`. The original audit bundle SHA-256 was `2f1d0759b1cca9ba24da8135c7df8631380de7086801cf2cabf6e90ceff54053`. The fresh audit manifest SHA-256 is `4852a4c3e2196e832ae4bd16543272600b5e19f8c9e5accf74ea8e8b3198091c` and the aggregate comparison receipt SHA-256 is `fe50b8e6a88b1334b10fbd8d3b01a44df6689dfc4846b2c97769faed21f11804`.

The JSON files in `math-methods/cards` are the editable source. Their examples are authored for this library. Keep model benchmarks, held-out evaluation items, and student submissions separate from the library.
