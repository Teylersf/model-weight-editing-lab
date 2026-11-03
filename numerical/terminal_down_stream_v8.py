"""V8 pure bounded-chunk F32 terminal-down edits; no files/native/model I/O.

D[out,in]=(5120,17408). C is native-dequantized D promoted to F32. E is C plus
U V.T rounded to F32. No assumption equates C's native forward behavior with P.
Only actual stored E-C values drive norms and streamed key-response estimates.
"""
from dataclasses import dataclass
import hashlib
import math

import numpy as np

DOUT, DIN = 5120, 17408
F32_MATRIX_BYTES = DOUT * DIN * 4
MAX_RANK, MAX_CHUNK_ROWS, MAX_KEY_BATCH = 8, 32, 128
MAX_FROBENIUS_CAP_FRACTION = 0.01
MAX_POSITIVE_RESIDUAL_CAP_FRACTION = 0.05


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _array(value, name, shape, *, f32=False):
    _require(type(value) is np.ndarray and value.shape == shape,
             f"{name} requires an exact ndarray with bounded shape{shape}")
    _require(value.dtype == np.float32 if f32 else value.dtype.kind in "iuf",
             f"{name} has an unsupported dtype")


def _copy_f64(value, name):
    try:
        with np.errstate(over="raise", invalid="raise"):
            result = np.array(value, dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
        raise ValueError(f"{name} cannot be represented as finite F64") from exc
    _require(np.isfinite(result).all(), f"{name} must be finite")
    return result


def _readonly(value):
    value.setflags(write=False)
    return value


def _fraction(value, name, maximum):
    _require(type(value) in (int, float, np.float32, np.float64), f"{name} requires a plain finite scalar")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be representable") from exc
    _require(math.isfinite(result) and 0 < result <= maximum,
             f"{name} must be positive and cannot weaken the fixed maximum{maximum}")
    return result


def _norm(value):
    """Scaled Euclidean/Frobenius norm; no unscaled squaring of large values."""
    scale = float(np.max(np.abs(value))) if value.size else 0.0
    if scale == 0:
        return 0.0
    result = scale * math.sqrt(float(np.sum((value / scale) ** 2)))
    _require(math.isfinite(result), "Nonfinite norm")
    return result


@dataclass(frozen=True)
class F32Chunk:
    row_start: int
    control: np.ndarray
    edited: np.ndarray
    intended_delta: np.ndarray
    actual_delta: np.ndarray
    report: dict


class RankUpdatePlan:
    """Bounded U[5120,r],V[17408,r]; never construct the full outer product."""
    def __init__(self, U, V, *, frobenius_cap_fraction):
        _require(type(U) is np.ndarray and U.ndim == 2 and U.shape[0] == DOUT,
                 "U must be an exact ndarray with5120 rows")
        rank = U.shape[1]
        _require(1 <= rank <= MAX_RANK, "Per-plan engineering rank bound is1..8")
        _array(U, "U", (DOUT, rank)); _array(V, "V", (DIN, rank))
        self.cap_fraction = _fraction(frobenius_cap_fraction, "frobenius_cap_fraction", MAX_FROBENIUS_CAP_FRACTION)
        self.U, self.V = _readonly(_copy_f64(U, "U")), _readonly(_copy_f64(V, "V"))
        self.rank = rank

    def materialize_chunk(self, C, *, row_start):
        _require(type(row_start) is int and 0 <= row_start < DOUT, "Invalid row_start")
        _require(type(C) is np.ndarray and C.ndim == 2 and 1 <= C.shape[0] <= MAX_CHUNK_ROWS,
                 "C must have1..32 rows")
        n = C.shape[0]
        _require(row_start + n <= DOUT, "Chunk exceeds5120 rows")
        _array(C, "C", (n, DIN), f32=True)
        _require(np.isfinite(C).all(), "C must contain finite native-dequantized F32 values")
        control = C.copy()
        try:
            with np.errstate(over="raise", invalid="raise", divide="raise"):
                intended = self.U[row_start:row_start + n] @ self.V.T
                edited = (control.astype(np.float64) + intended).astype(np.float32)
                # Preserve exact C bytes for zero requested entries, including-0.
                untouched = intended == 0
                edited[untouched] = control[untouched]
                actual = edited.astype(np.float64) - control.astype(np.float64)
                rounding = actual - intended
        except FloatingPointError as exc:
            raise ValueError("Nonfinite F32 materialization arithmetic") from exc
        _require(all(np.isfinite(a).all() for a in (edited, intended, actual, rounding)),
                 "Nonfinite chunk output")
        report = {
            "row_start": row_start, "rows": n, "columns": DIN, "rank": self.rank,
            "control_frobenius": _norm(control.astype(np.float64)),
            "intended_delta_frobenius": _norm(intended), "actual_delta_frobenius": _norm(actual),
            "rounding_error_frobenius": _norm(rounding),
            "rounded_away_nonzero_entries": int(np.count_nonzero((intended != 0) & (actual == 0))),
            "actual_changed_values": int(np.count_nonzero(actual)),
            "changed_F32_bit_patterns": int(np.count_nonzero(control.view(np.uint32) != edited.view(np.uint32))),
            "control_sha256": hashlib.sha256(control.tobytes(order="C")).hexdigest(),
            "edited_sha256": hashlib.sha256(edited.tobytes(order="C")).hexdigest(),
        }
        return F32Chunk(row_start, _readonly(control), _readonly(edited),
                        _readonly(intended), _readonly(actual), report)


class MatrixAudit:
    """Complete ordered coverage and intended/actual Frob gates against C."""
    def __init__(self, *, frobenius_cap_fraction):
        self.fraction = _fraction(frobenius_cap_fraction, "frobenius_cap_fraction", MAX_FROBENIUS_CAP_FRACTION)
        self.next_row, self.chunks, self.changed, self.rounded = 0, 0, 0, 0
        self.control_norm = self.intended_norm = self.actual_norm = self.rounding_norm = 0.0
        self._control_sha, self._edited_sha = hashlib.sha256(), hashlib.sha256()

    def add(self, chunk):
        _require(isinstance(chunk, F32Chunk) and chunk.row_start == self.next_row,
                 "Chunks must cover D once in order, with no gaps/overlap")
        n = chunk.control.shape[0]
        _require(1 <= n <= MAX_CHUNK_ROWS and self.next_row + n <= DOUT, "Invalid chunk extent")
        for array, name in ((chunk.control, "control"), (chunk.edited, "edited")):
            _array(array, name, (n, DIN), f32=True)
            _require(np.isfinite(array).all(), "Nonfinite audit chunk")
        actual = chunk.edited.astype(np.float64) - chunk.control.astype(np.float64)
        _array(chunk.intended_delta, "intended_delta", (n, DIN))
        _require(np.isfinite(chunk.intended_delta).all(), "Nonfinite intended update")
        self.control_norm = math.hypot(self.control_norm, _norm(chunk.control.astype(np.float64)))
        self.intended_norm = math.hypot(self.intended_norm, _norm(chunk.intended_delta))
        self.actual_norm = math.hypot(self.actual_norm, _norm(actual))
        self.rounding_norm = math.hypot(self.rounding_norm, _norm(actual - chunk.intended_delta))
        self._control_sha.update(chunk.control.tobytes(order="C"))
        self._edited_sha.update(chunk.edited.tobytes(order="C"))
        self.changed += int(np.count_nonzero(actual))
        self.rounded += int(np.count_nonzero((chunk.intended_delta != 0) & (actual == 0)))
        self.next_row += n; self.chunks += 1

    def finish(self):
        _require(self.next_row == DOUT, "Incomplete D coverage; all5120 rows required")
        _require(all(math.isfinite(x) for x in (self.control_norm, self.intended_norm, self.actual_norm, self.rounding_norm)),
                 "Nonfinite aggregate norms")
        cap = self.fraction * self.control_norm
        intended_ok, actual_ok = self.intended_norm <= cap, self.actual_norm <= cap
        return {
            "shape": [DOUT, DIN], "F32_bytes": F32_MATRIX_BYTES, "rows_covered": self.next_row,
            "chunks": self.chunks, "control_frobenius": self.control_norm,
            "intended_delta_frobenius": self.intended_norm, "actual_delta_frobenius": self.actual_norm,
            "rounding_error_frobenius": self.rounding_norm, "frobenius_cap_fraction": self.fraction,
            "frobenius_cap": cap, "intended_cap_pass": intended_ok, "actual_cap_pass": actual_ok,
            "numeric_matrix_gates_pass": intended_ok and actual_ok,
            "actual_changed_values": self.changed, "rounded_away_nonzero_entries": self.rounded,
            "control_matrix_F32_sha256": self._control_sha.hexdigest(),
            "edited_matrix_F32_sha256": self._edited_sha.hexdigest(),
            "control_native_baseline_equality_to_P_assumed": False, "candidate_accepted": False,
        }


@dataclass(frozen=True)
class ResidualEffects:
    delta_residual: np.ndarray
    report: dict


class ResponseAudit:
    """Compute A_rows @ actual_delta_D.T in bounded key batches.

    Inputs are keys just BEFORE terminal down projection and residuals from C.
    The result is exact stored-weight linear response accumulated in F64; native
    F32 GEMM rounding can differ and must be checked by actual C/E forward runs.
    """
    def __init__(self, A_control, residuals_C, positive_mask, *, positive_cap_fraction):
        _require(type(A_control) is np.ndarray and A_control.ndim == 2
                 and 1 <= A_control.shape[0] <= MAX_KEY_BATCH, "Key batch must contain1..128 states")
        n = A_control.shape[0]
        _array(A_control, "A_control", (n, DIN)); _array(residuals_C, "residuals_C", (n, DOUT))
        _require(type(positive_mask) is np.ndarray and positive_mask.shape == (n,)
                 and positive_mask.dtype == np.bool_, "positive_mask must be exact bool[n]")
        self.fraction = _fraction(positive_cap_fraction, "positive_cap_fraction", MAX_POSITIVE_RESIDUAL_CAP_FRACTION)
        self.keys = _readonly(_copy_f64(A_control, "A_control"))
        self.baseline = _readonly(_copy_f64(residuals_C, "residuals_C"))
        self.positive = _readonly(positive_mask.copy())
        self.effects = np.zeros((n, DOUT), dtype=np.float64)
        self.next_row = 0

    def add(self, chunk):
        _require(isinstance(chunk, F32Chunk) and chunk.row_start == self.next_row,
                 "Response chunks must cover D once in order")
        n = chunk.control.shape[0]
        _require(1 <= n <= MAX_CHUNK_ROWS and self.next_row + n <= DOUT, "Invalid response chunk extent")
        _array(chunk.control, "control", (n, DIN), f32=True); _array(chunk.edited, "edited", (n, DIN), f32=True)
        _require(np.isfinite(chunk.control).all() and np.isfinite(chunk.edited).all(), "Nonfinite response chunk")
        try:
            with np.errstate(over="raise", invalid="raise"):
                actual = chunk.edited.astype(np.float64) - chunk.control.astype(np.float64)
                effect = self.keys @ actual.T
        except FloatingPointError as exc:
            raise ValueError("Nonfinite key response arithmetic") from exc
        _require(np.isfinite(effect).all(), "Nonfinite key response")
        self.effects[:, self.next_row:self.next_row + n] = effect
        self.next_row += n

    def finish(self):
        _require(self.next_row == DOUT, "Incomplete response coverage")
        norms = np.array([_norm(row) for row in self.effects])
        base = np.array([_norm(row) for row in self.baseline])
        passed = norms <= self.fraction * base
        return ResidualEffects(_readonly(self.effects.copy()), {
            "states": len(base), "delta_residual_l2": norms.tolist(), "C_residual_l2": base.tolist(),
            "positive_mask": self.positive.tolist(), "positive_cap_fraction": self.fraction,
            "positive_state_caps_pass": bool(passed[self.positive].all()),
            "positive_cap_per_state_pass": passed[self.positive].tolist(),
            "response_uses_actual_stored_F32_weight_delta": True, "F64_linear_response_only": True,
            "native_C_E_GEMM_response_verified": False, "argmax_and_margin_preservation_verified": False,
            "candidate_accepted": False,
        })
