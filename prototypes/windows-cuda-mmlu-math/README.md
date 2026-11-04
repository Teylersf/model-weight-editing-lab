# Reproduce the MMLU mathematics evaluation

This example evaluates the full official high-school mathematics and college mathematics test splits. It uses 270 and 100 questions respectively, with the five official development examples for each subject. The benchmark measures multiple-choice accuracy on these public English-language splits. The model's pretraining overlap is unknown.

The prompt ends at the raw answer marker. The native Windows CUDA scorer evaluates the four exact leading-space answer tokens using next-token logits and selects the highest score. It checks that each answer is one token and appends cleanly to each prompt. The author evaluator used a legacy API with a top-100 fallback and could reduce the number of examples to fit its tokenizer. This reproduction uses full-vocabulary logits and keeps all five examples. Invalid and length-censored rows count in the full test-set denominator. [Benchmark paper](https://arxiv.org/abs/2009.03300) · [Author evaluation script](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/evaluate.py)

Keep downloaded and generated benchmark files in a scratch directory outside the repository. The Python script verifies the archive and four CSV digests and requires only the standard library. The native model process receives the prepared prompts. The grading step reads the test labels separately.

## Prepare prompts

Use Python 3.10 or later. Run the commands from a scratch directory, with the source paths and scratch paths set for your system.

~~~powershell
$source = 'C:\path\to\mmlu-math'
$work = 'C:\path\to\scratch'
curl.exe --fail --location --output "$work\data.tar" 'https://people.eecs.berkeley.edu/~hendrycks/data.tar'
python -I -B "$source\prepare_grade_mmlu_math.py" prepare --archive "$work\data.tar" --output "$work\mmlu-prepared"
~~~

## Build the Windows scorer

Use the x64 MSVC developer environment. Set the include paths to the headers matching your runtime and the library directory to their Windows import libraries. This source binds the Windows runtime used in the experiment, with GGML commit prefix 8642541b, CUDA0, and the matching CPU host library. The native log must record all 66 model layers offloaded to the GPU for grading.

~~~powershell
$llamaInclude = 'C:\path\to\llama-headers'
$ggmlInclude = 'C:\path\to\ggml-headers'
$imports = 'C:\path\to\matching-import-libraries'
cl.exe /nologo /W4 /WX /EHsc /O2 /std:c++17 /utf-8 /DGGML_SHARED /DLLAMA_SHARED "/I$llamaInclude" "/I$ggmlInclude" "$source\mmlu_choice_score.cpp" "/Fo:$work\mmlu_choice_score.obj" "/Fe:$work\mmlu_choice_score.exe" /link "/LIBPATH:$imports" llama.lib ggml.lib ggml-base.lib bcrypt.lib
~~~

## Score a checkpoint

Set the runtime directory to the matching llama.cpp and GGML DLL directory. Verify the model file's SHA-256 before and after scoring and use separate output files for each checkpoint. The no-model check prints the SHA-256 of each prepared prompt.

~~~powershell
$runtime = 'C:\path\to\runtime'
$model = 'C:\path\to\model.gguf'
$env:PATH = "$runtime;$env:PATH"
$manifest = "$work\mmlu-prepared\native-manifest.tsv"
& "$work\mmlu_choice_score.exe" --validate-only --manifest $manifest
& "$work\mmlu_choice_score.exe" --model $model --runtime-dir $runtime --manifest $manifest --output "$work\native-logits.json" 2> "$work\native-stderr.log"
python -I -B "$source\prepare_grade_mmlu_math.py" grade --archive "$work\data.tar" --preparation "$work\mmlu-prepared\preparation.json" --native "$work\native-logits.json" --native-log "$work\native-stderr.log" --output "$work\mmlu-scores.json"
~~~

Each subject reports its own full-split accuracy and row counts. The combined score is the micro-average over all 370 questions. Ties choose the first answer in A–D order and are counted separately. The scorer uses no chat template and generates no answer text.
