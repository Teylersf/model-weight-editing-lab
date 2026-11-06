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

The included tests found an expected card in the top three for all 74 development queries, with 71 ranked first. All five included off-topic queries returned no cards. A replay of the previously used retrieval challenge found an expected card in the top three for all 23 math queries, with 22 ranked first, and returned no cards for its five off-topic controls.

A separate audit froze 24 fresh math requests and 10 controls before searching the 257-card snapshot. With no filters and a limit of three, it matched an expected card first on **9/24** and in the top three on **17/24**. Top-three coverage was **8/12** in high school and **9/12** in undergraduate math. It returned no candidates for **3/6** off-topic requests and **0/4** underspecified requests. The audit measures retrieval. The tutor integration remains gated on better ranking and abstention.

The audited content revision was `7d637362b73b62da86d43501823fdb609525f023f0b88ead4946857a3c3a60a8` and the search revision was `9198708a52965007f1c2b584db916ac9b0e354105ede397cbb0a10c88918ae07`. The frozen audit bundle SHA-256 was `2f1d0759b1cca9ba24da8135c7df8631380de7086801cf2cabf6e90ceff54053`.

The JSON files in `math-methods/cards` are the editable source. Their examples are authored for this library. Keep model benchmarks, held-out evaluation items, and student submissions separate from the library.
