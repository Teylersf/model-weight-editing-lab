# V8 terminal-down F32 materialization and controls

This is a new pure numerical helper, not a GGUF writer or runtime adapter.
`terminal_down_stream_v8.py` accepts the native-dequantized F32 control tensor
D_C with shape(out,in)=(5120,17408), logically356515840 bytes=340MiB. A caller
provides U[5120,r],V[17408,r], r1..8. The helper computes at most32 output rows
at a time: intended_delta=U_rows@V.T, D_E=F32(D_C+intended_delta), then
actual_delta=F64(D_E)-F64(D_C). It never allocates a full5120x17408 outer product.
No model, file, native-library, backend, service, or network operation exists in
the module. Frozen older sources are unchanged.

```python
plan = RankUpdatePlan(U, V, frobenius_cap_fraction=0.01)
audit = MatrixAudit(frobenius_cap_fraction=0.01)
responses = ResponseAudit(A_control_rows, residuals_C, positive_mask,
                          positive_cap_fraction=0.05)
for row_start, C_chunk in caller_native_dequantized_F32_chunks:
    chunk = plan.materialize_chunk(C_chunk, row_start=row_start)
    audit.add(chunk)
    responses.add(chunk)
    # External reviewed writer may consume chunk.control/chunk.edited only after
    # all independent construction, physical-payload and native gates are met.
matrix_report = audit.finish()
effects = responses.finish()  # delta_residual[n_states,5120], plus diagnostics
```

Inputs require exact ndarrays with bounded dimensions, checked before conversion
or scans. U,V are copied to readonly F64; C chunks must already be finite F32.
Outputs are readonly arrays. Ordered audits reject missing/duplicate/out-of-order
rows. Matrix hashes cover complete C/E tensors in row-major F32 order. Intended
and actual Frobenius updates must each be at most1% of ||D_C||F. Caller-supplied
fractions can make this stricter, never weaker. Stable scaled norms and hypot
accumulation avoid overflow/underflow from direct norm squaring. No rescaling is
performed. Zero requested entries preserve their C bits, including negative0.

ResponseAudit accepts at most128 key rows[n,17408] per batch and residual_C rows
[n,5120], and computes A@actual_delta_D.T. It reports every state's residual-change
norm; positive states must stay within5% of their corresponding ||r_C||. More
states are handled in additional batches; no state may be silently omitted.
These are per-experiment gates and engineering allocation bounds, not conditions
to stop the wider research workstream.

The response uses the exact stored F32 weight difference in F64 arithmetic. It
does NOT certify native F32 GEMM output differences: multiply/reduction precision
can differ. Actual C/E terminal residuals and complete-prefix logits must still
be checked. Neither intended v·a_control=0 nor a small matrix norm proves native
control preservation. The synthetic receipt explicitly demonstrates a zero
intended guard response becoming-1 after F32 rounding.

## Required promotion/writer checks once the actual source is available

1. Independently pin immutable B/P, source GGUF and exact native library/build;
   parse and verify the actual terminal-down tensor name, dtype, dimensions,
   offsets, byte counts, alignment, non-overlap, and graph placement. No guessed
   original dtype, tail length, layer ID, or absolute offsets belong in code.
2. C contains the native-dequantized original D promoted to F32 with no fit. It
   has a changed dtype/storage layout. Quantized and F32 matmul can differ even
   when dequantized coefficients agree; ordinary full baseline inference on C
   is mandatory. Record P→C effects separately from C→E effects. Do not claim
   that control C equals P numerically or bytewise.
3. A new reviewed writer must whitelist exactly the D dtype change to F32 and
   mechanically required downstream offsets/alignment. All tensor names,
   dimensions, other dtypes, and ordinary metadata remain unchanged. Preserve
   every other tensor payload by independently hashed identity at its relocated
   offset; preserve original trailing/non-target bytes through a framed tail
   relocation proof. Record the precise allowed descriptor/padding changes.
4. C and E share the same promoted metadata/layout. E differs only inside the
   D tensor span; verify their complete untouched complement, every stored E
   chunk against materialization, actual matrix Frobenius norms by rereading
   physical C/E chunks, and complete coverage. A whole-file hash or a promised
   rank-one formula alone cannot replace these checks.
5. Protect source paths and existing candidates, use fresh independently owned
   derivatives, ensure B/P remain immutable, and pin source/data/plan/receipts.
   Record actual F32 E-C, intended delta, rounding error, row/state leakage and
   P/C/E hashes. Leave the original selected model unchanged during evaluation.
6. For fixed prefixes, capture native C upstream MLP keys and pre-down residual
   skip plus r_C. The chosen D must be terminal: these inputs must be verified
   independent of this D edit. Preserve all-prefix original greedy winners and
   frozen margins, independently check positive actual residual caps, and grade
   complete mathematical/format/completion outputs. No acceptance is inferred
   from this helper or from the fitting exemplar alone.

No I/O writer was implemented; actual Mac promotion source/metadata remain to be
reviewed before using such a writer.

## Quantized head-only/tail replay feasibility

The pinned public [GGML API](https://raw.githubusercontent.com/ggml-org/llama.cpp/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/include/ggml.h)
provides quantized ggml_mul_mat. The [backend API](https://raw.githubusercontent.com/ggml-org/llama.cpp/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/include/ggml-backend.h)
provides explicit backend initialization, operation-support checks, tensor
allocation and transfers. [Metal initialization](https://raw.githubusercontent.com/ggml-org/llama.cpp/8642541b255bfb5dc39cd351a178be09013a55d6/ggml/include/ggml-metal.h)
is public. Build against matching headers; do not guess internal tensor structs.
Actual Mac ABI/backend support and replay equivalence are not verified here.

output.weight Q4_K[5120,248320] uses715161600 packed bytes(~682MiB), versus
5085593600 bytes(~4.74GiB) fully F32. A dedicated suffix graph can use captured
upstream key+skip, one340MiB F32 D at a time, RMS normalization, and this unchanged
quantized head; all-vocabulary output is993280 bytes/state. After releasing the
full model, working weights are about1GiB rather than another full checkpoint.
This is a design, not an implemented or benchmarked GPU replay. Validate its
residual/logit outputs against native C at representative prefixes and relevant
batch/precision settings before trusting close ranking margins.

For guards, norm-based pruning needs a verified actual hidden change: if M bounds
every head-row norm, the original winner has row norm N and gap G, then
(N+M)||delta_h|| < G-required_margin bounds ranking drift in real arithmetic.
Include native numerical error allowances. A theoretical null key response or
the F64 weight-response estimate alone is not such a certificate. Remaining
states need actual all-vocabulary replay; positives always need full margins.
