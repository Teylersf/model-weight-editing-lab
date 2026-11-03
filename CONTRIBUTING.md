# Contributing

Useful contributions make an edit reproducible and its limits clear.

For a result, include:

1. Parent repository, revision, checkpoint SHA-256, tokenizer/template, and runtime commit.
2. The behavior you intended to change and the baseline failure.
3. Tensor names, shapes/orientation, original and final encodings, edit algorithm, and actual stored delta.
4. Which prompts and feedback selected the edit, which guided development, and which remained unseen.
5. Representation-only controls, native calibration, protected-context checks, and ordinary generated answers.
6. Full mathematical/format rubrics, latency and length measurements, regressions, and failed experiments.
7. Minimal commands, dependencies, hardware, memory needs, and source/data licensing.

Please use small synthetic fixtures for code changes. Do not commit model checkpoints, credentials, private logs, or unseen evaluation material. Keep numerical infrastructure checks separate from model-quality claims.

The introductory example uses Python's standard unittest runner:

```bash
python -m unittest discover -s tests -v
```

The advanced numerical checks run separately as documented in the README. Passing a synthetic check is not sufficient to claim that an edited model improved.
