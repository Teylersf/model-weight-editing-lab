# Windows CUDA ordinary generation runner

This runner takes a local GGUF and a UTF-8 prompt file. It runs generation on CUDA0 and records the prompt hash, token IDs, completion token count, and finish reason. The token count includes the sampled end-of-generation token.

The lab built this source with x64 MSVC 19.44 and ran it on an RTX 3090 with llama.cpp build 11960, commit `8642541b255bfb5dc39cd351a178be09013a55d6`, and GGML 0.28.0. The source SHA-256 is `8b7a7def11cb007725764b0ef52b356bdef3c2c0ebc4940e330cf33535bdf5dc`.

## Build

Open an x64 Visual Studio developer command prompt. Use headers and x64 import libraries that match the installed runtime. The lab generated `llama.lib`, `ggml.lib`, and `ggml-base.lib` with MSVC `lib.exe /machine:x64 /def:...` from the named code exports of the corresponding DLLs, inspected with `dumpbin /exports`. The runtime directory also supplies `ggml-cuda.dll`, `ggml-cpu-x64.dll`, and their dependencies.

```cmd
cl /nologo /W4 /WX /EHsc /O2 /std:c++17 /utf-8 /DGGML_SHARED /DLLAMA_SHARED ^
  /I"path\to\llama-headers" /I"path\to\ggml-headers" ^
  math_trace_runner_3072_win.cpp /Fe:math_trace_runner_3072_win.exe ^
  /link /LIBPATH:"path\to\import-libraries" llama.lib ggml.lib ggml-base.lib bcrypt.lib
```

The pinned llama.cpp source contains the public C API headers and matching build configuration. [llama.cpp at the pinned revision](https://github.com/ggml-org/llama.cpp/tree/8642541b255bfb5dc39cd351a178be09013a55d6)

## Run one prompt

Supply your own absolute paths. Use a fresh output path in a private directory. The JSON and runtime log can contain the supplied prompt and generated text.

```powershell
$runtime = 'C:\path\to\llama-runtime'
$model = 'C:\path\to\model.gguf'
$prompt = 'C:\path\to\rendered-prompt.utf8'
$output = 'C:\path\to\fresh-result.json'
$savedPath = $env:Path
try {
    $env:Path = "$runtime;$savedPath"
    & '.\math_trace_runner_3072_win.exe' --check-cuda --runtime-dir $runtime
    if ($LASTEXITCODE -ne 0) { throw 'CUDA0 check failed' }
    & '.\math_trace_runner_3072_win.exe' --runtime-dir $runtime --model $model `
        --prompt-file $prompt --output $output --raw --ctx 4096 --max-tokens 3072 --seed 42
    if ($LASTEXITCODE -ne 0) { throw 'Generation failed' }
} finally {
    $env:Path = $savedPath
}
```

`--raw` consumes the supplied bytes as the rendered prompt. Use the same serialized prompt and settings across baseline and candidate runs. Check the loader log for actual layer placement and compare prompt token IDs before comparing completions. Different backends can produce different completions with the same checkpoint and prompt IDs.

## Verify the reviewed rank-two proof pair

The [proof pair manifest](../../evidence/rank-two-ordinary-proof-pair.json) publishes the checkpoint hash, exact prompt and output identities, and CUDA settings from the reviewed run. With the archived checkpoint and two raw rendered prompts, rerun the pair using the pinned runner. Run from the repository root and use a fresh private output directory.

```powershell
$proofPair = Get-Content -Raw evidence/rank-two-ordinary-proof-pair.json | ConvertFrom-Json
# Supply paths for $runner, $runtime, $model, $intervalPrompt, $eulerPrompt,
# $result and $log. The matching runtime DLLs must be on PATH.
& $runner --runtime-dir $runtime --model $model `
    --prompt-file $intervalPrompt --id $proofPair.cases[0].id `
    --prompt-file $eulerPrompt --id $proofPair.cases[1].id `
    --raw --ctx 4096 --max-tokens 3072 --seed 42 --threads 4 `
    --batch 64 --temperature 0 --gpu-layers -1 --output $result 2> $log
if ($LASTEXITCODE -ne 0) { throw 'Generation failed' }
python examples/verify_cuda_proof_pair.py `
    --manifest evidence/rank-two-ordinary-proof-pair.json `
    --model $model --result $result --log $log
```

Use PowerShell 7 with UTF-8 log output. The verifier accepts Windows and Unix line endings. It matches the reviewed visible proof bytes, every prompt and completion token ID, and every live token piece. Token IDs are hashed as consecutive signed little-endian 32-bit integers. The completion count includes the natural end token. The whole-generation and final hashes exclude that end token.

The public files supply the runner source, recipe and verification inputs in the form of hashes. The checkpoint, rendered prompts and transcripts are local research inputs required for an exact rerun. Mathematical grading was performed independently on the local visible proofs. Exact byte matching transfers that review to a rerun of this pair. The broader regression results are reported separately in the [case study](../../docs/case-study.md).
