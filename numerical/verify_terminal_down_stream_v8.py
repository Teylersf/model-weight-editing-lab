"""Synthetic340MiB logical matrix verification with at most32 rows allocated."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import terminal_down_stream_v8 as stream


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def verify():
    U = np.zeros((stream.DOUT, 2)); V = np.zeros((stream.DIN, 2))
    U[0, 0] = 1.; V[0, 0], V[1, 0] = 1., -1.
    U[1, 1] = 2 ** -30; V[2, 1] = 1.
    plan = stream.RankUpdatePlan(U, V, frobenius_cap_fraction=.01)
    audit = stream.MatrixAudit(frobenius_cap_fraction=.01)
    strict = stream.MatrixAudit(frobenius_cap_fraction=1e-9)
    keys = np.zeros((2, stream.DIN)); keys[0, :2] = [1., -1.]; keys[1, :2] = [1., 1.]
    residuals_C = np.ones((2, stream.DOUT))
    positive = np.array([True, False])
    responses = stream.ResponseAudit(keys, residuals_C, positive, positive_cap_fraction=.05)
    strict_responses = stream.ResponseAudit(keys, residuals_C, positive, positive_cap_fraction=1e-6)
    naive_control_sha, naive_edited_sha = hashlib.sha256(), hashlib.sha256()
    rejected = []
    def bad(label, action):
        try:
            action()
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError("Invalid input accepted: " + label)
    bad("incomplete_coverage", audit.finish)
    first = None
    for start in range(0, stream.DOUT, stream.MAX_CHUNK_ROWS):
        C = np.ones((min(stream.MAX_CHUNK_ROWS, stream.DOUT - start), stream.DIN), dtype=np.float32)
        C[:, -1] = -0.0
        if start == 0:
            C[0, 0] = 1e8  #+1 rounds away here; the-1 at the other entry survives.
        chunk = plan.materialize_chunk(C, row_start=start)
        check(chunk.control.nbytes <= 32 * stream.DIN * 4, "Chunk bound exceeded")
        check(not chunk.edited.flags.writeable, "Chunk output mutable")
        # Independent per-row explicit rank sum, avoiding a full matrix product.
        for local in range(len(C)):
            intended = np.zeros(stream.DIN)
            for rank in range(2):
                intended += U[start + local, rank] * V[:, rank]
            expected = (C[local].astype(np.float64) + intended).astype(np.float32)
            expected[intended == 0] = C[local, intended == 0]
            np.testing.assert_array_equal(expected.view(np.uint32), chunk.edited[local].view(np.uint32))
        np.testing.assert_array_equal(chunk.actual_delta,
                                     chunk.edited.astype(np.float64) - C.astype(np.float64))
        check(np.signbit(chunk.edited[:, -1]).all(), "Unchanged negative zero bits lost")
        audit.add(chunk); strict.add(chunk); responses.add(chunk); strict_responses.add(chunk)
        naive_control_sha.update(C.tobytes()); naive_edited_sha.update(chunk.edited.tobytes())
        if first is None:
            first = chunk
            check(chunk.intended_delta[0, :2].tolist() == [1., -1.], "Bad intended rank1 values")
            check(chunk.actual_delta[0, :2].tolist() == [0., -1.], "F32 rounding not captured")
            check(chunk.actual_delta[1, 2] == 0, "Tiny update should round away")
            bad("duplicate_coverage", lambda: audit.add(chunk))
    result, strict_result = audit.finish(), strict.finish()
    response, strict_response = responses.finish(), strict_responses.finish()
    check(result["rows_covered"] == 5120 and result["F32_bytes"] == 356515840, "FullD dimensions wrong")
    check(result["numeric_matrix_gates_pass"] and not strict_result["numeric_matrix_gates_pass"], "Matrix cap gates wrong")
    check(result["actual_delta_frobenius"] == 1.0, "Actual Frobenius norm incorrect")
    check(math.isclose(result["intended_delta_frobenius"], math.sqrt(2.0), rel_tol=1e-14), "Intended norm incorrect")
    check(result["rounded_away_nonzero_entries"] == 2, "Rounded-away count wrong")
    check(result["control_matrix_F32_sha256"] == naive_control_sha.hexdigest()
          and result["edited_matrix_F32_sha256"] == naive_edited_sha.hexdigest(), "Stream hashes wrong")
    check(response.delta_residual[0, 0] == 1.0 and response.delta_residual[1, 0] == -1.0,
          "Actual response not independently correct")
    check(np.count_nonzero(response.delta_residual) == 2, "Unexpected residual leakage")
    check(keys[1] @ V[:, 0] == 0 and response.delta_residual[1, 0] != 0,
          "Rounding should demonstrate loss of theoretical guard nullity")
    check(response.report["positive_state_caps_pass"] and not strict_response.report["positive_state_caps_pass"],
          "Positive residual cap gates wrong")
    for magnitude in (1e300, 1e-300):
        check(math.isclose(stream._norm(np.array([magnitude, magnitude])), math.sqrt(2) * magnitude,
                           rel_tol=1e-14), "Scaled norm unstable")
    zero = stream.RankUpdatePlan(np.zeros((stream.DOUT, 1)), np.zeros((stream.DIN, 1)), frobenius_cap_fraction=.01)
    Czero = np.ones((1, stream.DIN), dtype=np.float32); Czero[0, -1] = -0.
    noedit = zero.materialize_chunk(Czero, row_start=0)
    check(Czero.tobytes() == noedit.edited.tobytes() and not np.any(noedit.actual_delta), "Zero control bytes changed")
    overflow_U = np.zeros((stream.DOUT, 1)); overflow_U[0, 0] = 3e38
    overflow_V = np.zeros((stream.DIN, 1)); overflow_V[0, 0] = 1.
    overflow = stream.RankUpdatePlan(overflow_U, overflow_V, frobenius_cap_fraction=.01)
    extreme_C = np.full((1, stream.DIN), np.float32(3e38), dtype=np.float32)
    bad("F32_overflow", lambda: overflow.materialize_chunk(extreme_C, row_start=0))
    bad("weaker_matrix_cap", lambda: stream.MatrixAudit(frobenius_cap_fraction=.011))
    bad("weaker_positive_cap", lambda: stream.ResponseAudit(keys, residuals_C, positive, positive_cap_fraction=.051))
    bad("nonfinite_factor", lambda: stream.RankUpdatePlan(np.full((stream.DOUT, 1), np.nan), overflow_V, frobenius_cap_fraction=.01))
    huge_U = np.broadcast_to(np.array(0.), (10_000_000, 8))
    huge_C = np.broadcast_to(np.array(0., dtype=np.float32), (10_000_000, stream.DIN))
    huge_keys = np.broadcast_to(np.array(0.), (10_000_000, stream.DIN))
    class Bomb:
        def __array__(self, *a, **k):
            raise AssertionError("Arbitrary conversion protocol invoked")
    original_array, original_finite = np.array, np.isfinite
    calls = []
    def forbidden(*a, **k):
        calls.append(1); raise AssertionError("Invalid shape reached allocation/scan")
    try:
        np.array = np.isfinite = forbidden
        bad("oversized_U", lambda: stream.RankUpdatePlan(huge_U, overflow_V, frobenius_cap_fraction=.01))
        bad("arbitrary_U", lambda: stream.RankUpdatePlan(Bomb(), overflow_V, frobenius_cap_fraction=.01))
        bad("oversized_C", lambda: plan.materialize_chunk(huge_C, row_start=0))
        bad("wrong_C_dtype", lambda: plan.materialize_chunk(np.zeros((1, stream.DIN)), row_start=0))
        bad("oversized_key_batch", lambda: stream.ResponseAudit(huge_keys, residuals_C, positive, positive_cap_fraction=.05))
    finally:
        np.array, np.isfinite = original_array, original_finite
    check(not calls, "Preconversion guards failed")
    base = Path(__file__).parent
    return {"verification": "passed", "synthetic_only": True, "model_or_native_or_Mac_actions": False,
            "full_logical_matrix_bytes": stream.F32_MATRIX_BYTES, "maximum_rows_per_chunk": 32,
            "matrix_audit": result, "stronger_cap_rejected": strict_result,
            "actual_key_response": response.report, "stronger_positive_cap_rejected": strict_response.report,
            "control_nullity_broken_by_F32_rounding_demonstrated": True,
            "zero_edit_F32_bytes_exact": True, "scaled_norm_large_and_small_passed": True,
            "invalid_inputs_rejected": rejected, "preconversion_invalid_cases": 5,
            "preconversion_allocation_or_scan_calls": len(calls),
            "source_files": {name: hashlib.sha256((base / name).read_bytes()).hexdigest()
                             for name in ("terminal_down_stream_v8.py", "verify_terminal_down_stream_v8.py")},
            "limitations": "Pure numerical stored-weight response; native C/E GEMM rounding, actual residuals, full logits/margins, GGUF relocation and payload identity remain unverified external gates."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    result = verify()
    if args.receipt:
        args.receipt.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"verification": result["verification"], "logical_matrix_bytes": result["full_logical_matrix_bytes"],
                      "rows_covered": result["matrix_audit"]["rows_covered"],
                      "actual_Frobenius": result["matrix_audit"]["actual_delta_frobenius"],
                      "rounding_broke_guard_nullity": result["control_nullity_broken_by_F32_rounding_demonstrated"],
                      "invalid_inputs": len(result["invalid_inputs_rejected"]), "preconversion_calls": len(calls) if 'calls' in globals() else result["preconversion_allocation_or_scan_calls"]}))
