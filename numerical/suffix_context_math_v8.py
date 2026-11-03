"""V8 bounded float64 suffix/context math; NumPy only, no model/file/native I/O.

Exact means the supplied F64 RMSNorm/selected-head formula, not an assertion of
native kernel equivalence. Native calibration and complete-answer validation are
external prerequisites. Context projection only protects the supplied guards.
"""
from dataclasses import dataclass
import numpy as np

MAX_DOUT, MAX_DIN, MAX_SELECTED = 5120, 17408, 128
MAX_CONTEXT_GUARDS = 4096
MIN_SEPARATION_RATIO = 1e-3
MAX_GUARD_KEY_RESPONSE = 1e-6
KEY_POSITIVE_RESPONSE_TOL = 1e-8
NATIVE_H_ABS_TOL, NATIVE_LOGIT_ABS_TOL = 1e-5, 1e-4
GRAD_REL_TOL, TARGET_MARGIN_TOL, BISECTIONS = 1e-12, 1e-8, 64
_REAL_TYPES = (int, float, np.int8, np.int16, np.int32, np.int64,
               np.uint8, np.uint16, np.uint32, np.uint64,
               np.float16, np.float32, np.float64, np.longdouble)


def _vector_meta(value, name, length):
    if type(value) is np.ndarray:
        if value.shape != (length,) or value.dtype.kind not in "iuf":
            raise ValueError(f"{name} must be a real vector of length {length}")
    elif type(value) in (list, tuple):
        if len(value) != length:
            raise ValueError(f"{name} must have length {length}")
    else:
        raise ValueError(f"{name} requires exact ndarray/list/tuple")


def _vector_size(value, name, maximum):
    if type(value) is np.ndarray:
        if value.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        n = value.shape[0]
    elif type(value) in (list, tuple):
        n = len(value)
    else:
        raise ValueError(f"{name} requires exact ndarray/list/tuple")
    if not 1 <= n <= maximum:
        raise ValueError(f"{name} exceeds the bounded width")
    _vector_meta(value, name, n)
    return n


def _matrix_meta(value, name, width, maximum, minimum=0):
    if type(value) is np.ndarray:
        if (value.ndim != 2 or value.shape[1] != width or value.dtype.kind not in "iuf"
                or not minimum <= value.shape[0] <= maximum):
            raise ValueError(f"{name} has invalid bounded shape/dtype")
    elif type(value) in (list, tuple):
        if not minimum <= len(value) <= maximum:
            raise ValueError(f"{name} exceeds bounded row count")
        for row in value:
            _vector_meta(row, name + " row", width)
    else:
        raise ValueError(f"{name} requires exact ndarray/list/tuple")
    return len(value)


def _scalar(value, name, *, positive=False):
    if type(value) not in _REAL_TYPES:
        raise ValueError(f"{name} requires a plain finite scalar")
    try:
        x = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} is not representable") from exc
    if not np.isfinite(x) or (positive and x <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return x


def _prepare(specs):
    # Callers validate ALL metadata before this bounded scalar/finite scan.
    for value, name, shape in specs:
        if type(value) is not np.ndarray:
            for row in value if len(shape) == 2 else (value,):
                if type(row) in (list, tuple) and any(type(x) not in _REAL_TYPES for x in row):
                    raise ValueError(f"{name} requires plain numeric cells")
    result = []
    for value, name, shape in specs:
        try:
            with np.errstate(over="raise", invalid="raise"):
                arr = np.asarray(value, dtype=np.float64).reshape(shape)
        except (TypeError, ValueError, OverflowError, FloatingPointError) as exc:
            raise ValueError(f"{name} cannot be represented as finite F64") from exc
        if not np.isfinite(arr).all():
            raise ValueError(f"{name} must be finite")
        result.append(arr)
    return result


def _rms(r, gamma, epsilon):
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            scale = float(np.sqrt((r @ r) / len(r) + epsilon))
            h = gamma * r / scale
    except FloatingPointError as exc:
        raise ValueError("RMS suffix arithmetic overflow") from exc
    if not np.isfinite(scale) or not np.isfinite(h).all():
        raise ValueError("Nonfinite RMS suffix arithmetic")
    return h, scale


def rms_hidden(r, gamma, epsilon):
    d = _vector_size(r, "r", MAX_DOUT)
    _vector_meta(gamma, "gamma", d)
    epsilon = _scalar(epsilon, "epsilon", positive=True)
    r, gamma = _prepare([(r, "r", (d,)), (gamma, "gamma", (d,))])
    try:
        return _rms(r, gamma, epsilon)[0]
    except FloatingPointError as exc:
        raise ValueError("RMS suffix arithmetic overflow") from exc


def selected_logits(r, gamma, epsilon, selected_rows):
    d = _vector_size(r, "r", MAX_DOUT)
    _vector_meta(gamma, "gamma", d)
    k = _matrix_meta(selected_rows, "selected_rows", d, MAX_SELECTED, 1)
    epsilon = _scalar(epsilon, "epsilon", positive=True)
    r, gamma, w = _prepare([(r, "r", (d,)), (gamma, "gamma", (d,)),
                             (selected_rows, "selected_rows", (k, d))])
    try:
        with np.errstate(over="raise", invalid="raise"):
            out = w @ _rms(r, gamma, epsilon)[0]
        if not np.isfinite(out).all():
            raise ValueError("Nonfinite selected logits")
        return out
    except FloatingPointError as exc:
        raise ValueError("Selected-logit arithmetic overflow") from exc


def pair_logit_gradient(r, gamma, epsilon, w_positive, w_negative):
    """Gradient of (w_positive-w_negative) dot RMSNorm(r) with respect to r."""
    d = _vector_size(r, "r", MAX_DOUT)
    for value, name in ((gamma, "gamma"), (w_positive, "w_positive"), (w_negative, "w_negative")):
        _vector_meta(value, name, d)
    epsilon = _scalar(epsilon, "epsilon", positive=True)
    r, gamma, wp, wm = _prepare([(r, "r", (d,)), (gamma, "gamma", (d,)),
                                 (w_positive, "w_positive", (d,)), (w_negative, "w_negative", (d,))])
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            _, scale = _rms(r, gamma, epsilon)
            k = gamma * (wp - wm)
            g = k / scale - r * ((k @ r) / (d * scale ** 3))
        if not np.isfinite(g).all():
            raise ValueError("Nonfinite pair gradient")
        return g
    except (FloatingPointError, OverflowError) as exc:
        raise ValueError("Pair-gradient arithmetic overflow") from exc


def calibrate_suffix(r, gamma, epsilon, selected_rows, native_h, native_logits):
    d = _vector_size(r, "r", MAX_DOUT)
    _vector_meta(gamma, "gamma", d); _vector_meta(native_h, "native_h", d)
    k = _matrix_meta(selected_rows, "selected_rows", d, MAX_SELECTED, 1)
    _vector_meta(native_logits, "native_logits", k)
    epsilon = _scalar(epsilon, "epsilon", positive=True)
    r, gamma, w, nh, nz = _prepare([(r, "r", (d,)), (gamma, "gamma", (d,)),
        (selected_rows, "selected_rows", (k, d)), (native_h, "native_h", (d,)), (native_logits, "native_logits", (k,))])
    predicted_h = rms_hidden(r, gamma, epsilon)
    predicted_z = selected_logits(r, gamma, epsilon, w)
    h_error, z_error = float(np.max(np.abs(predicted_h - nh))), float(np.max(np.abs(predicted_z - nz)))
    if not np.isfinite(h_error) or not np.isfinite(z_error):
        raise ValueError("Nonfinite calibration error")
    return dict(h_max_abs_error=h_error, selected_logits_max_abs_error=z_error,
                h_abs_tolerance=NATIVE_H_ABS_TOL, logit_abs_tolerance=NATIVE_LOGIT_ABS_TOL,
                calibration_pass=bool(h_error <= NATIVE_H_ABS_TOL and z_error <= NATIVE_LOGIT_ABS_TOL),
                verifies="supplied suffix/projection snapshots only; not model quality")


def nll_from_full_vocab_logz(native_full_logz, native_gold_logits):
    """Soft sequence objective from ACTUAL full-vocabulary logZ, never a shortlist.

    Residual edits change all logits: do not reuse parent's logZ for an edited
    suffix. The caller streams native head replay and supplies corresponding
    full logZ and gold logits. Valid alternative continuations need their own
    explicitly declared teacher sequences; NLL alone is not mathematical truth.
    """
    n = _vector_size(native_full_logz, "native_full_logz", MAX_CONTEXT_GUARDS)
    _vector_meta(native_gold_logits, "native_gold_logits", n)
    z, gold = _prepare([(native_full_logz, "native_full_logz", (n,)),
                         (native_gold_logits, "native_gold_logits", (n,))])
    loss = z - gold
    if not np.isfinite(loss).all() or (loss < 0).any():
        raise ValueError("Full-vocabulary logZ must be finite and at least the gold logit")
    total, mean = float(np.sum(loss)), float(np.mean(loss))
    if not np.isfinite(total) or not np.isfinite(mean):
        raise ValueError("Sequence NLL aggregation overflow")
    return dict(per_token_nll=loss, sum_nll=total, mean_nll=mean,
                tokens=n, selected_softmax_is_not_full_model_CE=True)


@dataclass(frozen=True)
class ContextKey:
    v: np.ndarray | None
    diagnostics: dict


def project_context_key(a_positive, early_guards):
    """Nullspace key normalized by a_positive@v=1; invalid keys return None.

    Dense projection accepts at most4096 guard rows. At actual Din17408, F64
    inputs alone can reach544MiB; unload the full model before large dense SVD.
    Whole-prefix audits outside the supplied matrix remain explicitly external.
    """
    d = _vector_size(a_positive, "a_positive", MAX_DIN)
    n = _matrix_meta(early_guards, "early_guards", d, MAX_CONTEXT_GUARDS)
    a, A = _prepare([(a_positive, "a_positive", (d,)), (early_guards, "early_guards", (n, d))])
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            norm_a = float(np.linalg.norm(a))
            if n:
                _, s, vt = np.linalg.svd(A, full_matrices=False)
                tol = np.finfo(float).eps * max(A.shape) * s[0]
                rank = int(np.count_nonzero(s > tol))
                basis = vt[:rank]
                residual = a - (a @ basis.T) @ basis
            else:
                s, tol, rank, residual = np.array([]), 0.0, 0, a.copy()
            residual_norm = float(np.linalg.norm(residual))
            ratio = residual_norm / norm_a if norm_a else 0.0
            denominator = float(a @ residual)
            flags = []
            if not norm_a or ratio < MIN_SEPARATION_RATIO or denominator <= 0:
                flags.append("no_robust_positive_separation")
            v = residual / denominator if not flags else None
            response = float(a @ v) if v is not None else None
            leak = A @ v if v is not None else None
            max_leak = float(np.max(np.abs(leak))) if leak is not None and n else (0.0 if v is not None else None)
            key_norm = float(np.linalg.norm(v)) if v is not None else None
            if v is not None and (not np.isfinite(v).all()
                                  or not all(np.isfinite(x) for x in (response, key_norm, max_leak))):
                raise ValueError("Nonfinite recomputed context-key diagnostics")
            if v is not None and (abs(response - 1) > KEY_POSITIVE_RESPONSE_TOL
                                  or max_leak > MAX_GUARD_KEY_RESPONSE):
                flags.append("recomputed_key_response_or_guard_residual_failed")
                v = None
    except (FloatingPointError, np.linalg.LinAlgError) as exc:
        raise ValueError("Context projection failed numerically") from exc
    if not all(np.isfinite(x) for x in (norm_a, residual_norm, ratio, denominator)):
        raise ValueError("Nonfinite context diagnostics")
    report = dict(guard_rows=n, input_width=d, guard_rank=rank, rank_tolerance=float(tol),
                  guard_singular_values=s.tolist(), positive_norm=norm_a,
                  projected_positive_norm=residual_norm, separation_ratio=ratio,
                  minimum_separation_ratio=MIN_SEPARATION_RATIO, normalization_denominator=denominator,
                  positive_response=response, maximum_recomputed_guard_response=max_leak,
                  maximum_allowed_guard_response=MAX_GUARD_KEY_RESPONSE,
                  key_l2=key_norm if v is not None else None,
                  flags=flags, valid_key=v is not None, protects_only_supplied_guards=True,
                  whole_prefix_and_native_F32_controls_pending=True)
    if v is not None:
        v.setflags(write=False)
    return ContextKey(v, report)


@dataclass(frozen=True)
class ResidualStep:
    u: np.ndarray
    diagnostics: dict


def solve_pair_residual_step(r, gamma, epsilon, w_positive, w_negative, *,
                             target_margin, max_residual_l2, direction="tangent_gradient"):
    """Smallest exact-RMS step to a target on ONE fixed improving direction.

    Direction is frozen gradient or radial-tangent gradient. Analytic peak plus
    64 bisections replaces a dose sweep. Caller freezes the target/cap before fit.
    A missed target is a directional/cap failure, not global infeasibility.
    """
    d = _vector_size(r, "r", MAX_DOUT)
    for value, name in ((gamma, "gamma"), (w_positive, "w_positive"), (w_negative, "w_negative")):
        _vector_meta(value, name, d)
    epsilon = _scalar(epsilon, "epsilon", positive=True)
    target = _scalar(target_margin, "target_margin")
    cap = _scalar(max_residual_l2, "max_residual_l2")
    if cap < 0 or type(direction) is not str or direction not in ("gradient", "tangent_gradient"):
        raise ValueError("Nonnegative cap and a supported frozen direction are required")
    r, gamma, wp, wm = _prepare([(r, "r", (d,)), (gamma, "gamma", (d,)),
                                 (w_positive, "w_positive", (d,)), (w_negative, "w_negative", (d,))])
    k = gamma * (wp - wm)
    def margin(tau, q):
        return float(k @ _rms(r + tau * q, np.ones(d), epsilon)[0])
    baseline = margin(0, np.zeros(d))
    g = pair_logit_gradient(r, gamma, epsilon, wp, wm)
    r2 = float(r @ r)
    if direction == "tangent_gradient" and r2:
        g = g - r * ((r @ g) / r2)
    gn = float(np.linalg.norm(g))
    gradient_threshold = GRAD_REL_TOL * max(1.0, float(np.linalg.norm(k)) / _rms(r, gamma, epsilon)[1])
    tau, peak_tau, peak_margin = 0.0, 0.0, baseline
    reason = "target_already_met" if baseline >= target else "direction_not_robustly_improving"
    q = np.zeros(d)
    if baseline < target and gn > gradient_threshold and cap > 0:
        q = g / gn
        aa, bb, cc = float(k @ r), float(k @ q), float(r @ q)
        s2 = r2 / d + epsilon
        n0, n1 = bb * s2 - aa * cc / d, (bb * cc - aa) / d
        peak_tau = min(cap, max(0.0, -n0 / n1)) if n1 < 0 else cap
        peak_margin = margin(peak_tau, q)
        if peak_margin >= target:
            lo, hi = 0.0, peak_tau
            for _ in range(BISECTIONS):
                mid = (lo + hi) / 2
                if margin(mid, q) >= target:
                    hi = mid
                else:
                    lo = mid
            tau, reason = hi, "target_reached_on_frozen_direction"
        else:
            tau, reason = peak_tau, "target_not_reached_within_direction_and_cap"
    u = tau * q
    achieved, norm = margin(tau, q), float(np.linalg.norm(u))
    if not np.isfinite(u).all() or not all(np.isfinite(x) for x in (achieved, norm, peak_margin, gn)):
        raise ValueError("Nonfinite residual-step result")
    passed = bool(achieved >= target - TARGET_MARGIN_TOL and norm <= cap)
    u.setflags(write=False)
    return ResidualStep(u, dict(direction=direction, baseline_margin=baseline, target_margin=target,
        achieved_margin=achieved, residual_step_l2=norm, residual_cap_l2=cap,
        residual_cap_pass=bool(norm <= cap), target_reached=passed, stop_reason=reason,
        direction_gradient_l2=gn, gradient_threshold=gradient_threshold,
        exact_line_peak_tau=peak_tau, exact_line_peak_margin=peak_margin,
        bisections=BISECTIONS, target_numeric_tolerance=TARGET_MARGIN_TOL,
        global_optimum_established=False, materialized_F32_and_all_control_gates_pending=True))
