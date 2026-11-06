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

The included tests found an expected card in the top three for all 74 development queries, with 71 ranked first. All five included off-topic queries returned no cards. A replay of the previously used retrieval challenge found an expected card in the top three for all 23 math queries, with 22 ranked first, and returned no cards for its five off-topic controls. Earlier search changes used that challenge. These results cover regression tests. Before tuning tool use, freeze a new evaluation set that includes ambiguous and out-of-scope requests.

The JSON files in `math-methods/cards` are the editable source. Their examples are authored for this library. Keep model benchmarks, held-out evaluation items, and student submissions separate from the library.
