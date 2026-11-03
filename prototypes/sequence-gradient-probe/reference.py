"""Tiny decoded-linear sequence-gradient reference; no model/runtime operations.

The native Q4_K CPU forward first quantizes its activation to Q8_K.  Its
OUT_PROD pullback uses decoded weights.  We check that pullback with a FIXED
cotangent, separately from the differentiable decoded-linear mean-CE model.
Neither is claimed to differentiate the native activation quantizer.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

SCHEMA = "synthetic-q4k-sequence-gradient-probe-v1"
MAX_JSON_BYTES = 1024 * 1024
NATIVE_ATOL, NATIVE_RTOL = 5e-5, 5e-5
EPS = 1e-3


def array(value, name, shape):
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"Invalid finite tiny array: {name}, expected {shape}")
    return result


def prepare(document):
    if document.get("schema") != SCHEMA:
        raise ValueError("Unexpected synthetic fixture schema")
    f = document["fixtures"]
    w = np.asarray(f["head_decoded_f32"], dtype=np.float64)
    if w.ndim != 2:
        raise ValueError("Head requires [vocab,hidden]")
    vocab, hidden = w.shape
    base = np.asarray(f["base_r_f32"], dtype=np.float64)
    a = np.asarray(f["a_f32"], dtype=np.float64)
    u = np.asarray(f["u_f32"], dtype=np.float64)
    if base.ndim != 2 or a.ndim != 2 or u.ndim != 2:
        raise ValueError("BaseR/A/U require two dimensions")
    batch, din, rank = base.shape[0], a.shape[1], u.shape[1]
    if not (1 <= batch <= 8 and 1 <= din <= 32 and 1 <= rank <= 4
            and 2 <= vocab <= 64 and 1 <= hidden <= 512):
        raise ValueError("Fixture exceeds the synthetic-only bounds")
    out = {
        "w": array(w, "head_decoded_f32", (vocab, hidden)),
        "base": array(base, "base_r_f32", (batch, hidden)),
        "gamma": array(f["gamma_f32"], "gamma_f32", (hidden,)),
        "a": array(a, "a_f32", (batch, din)),
        "u": array(u, "u_f32", (hidden, rank)),
        "v": array(f["v_f32"], "v_f32", (rank, din)),
    }
    targets = f["target_ids"]
    if (not isinstance(targets, list) or len(targets) != batch
            or any(type(x) is not int or not 0 <= x < vocab for x in targets)):
        raise ValueError("Targets require tiny integer vocabulary IDs")
    out["targets"] = np.asarray(targets, dtype=np.int64)
    epsilon = float(document["epsilon"])
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("Positive finite epsilon required")
    out["epsilon"] = epsilon
    return out


def probabilities(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    exponential = np.exp(shifted)
    return exponential / exponential.sum(axis=1, keepdims=True)


def ce(logits, targets):
    maximum = logits.max(axis=1)
    logz = maximum + np.log(np.exp(logits - maximum[:, None]).sum(axis=1))
    return float(np.mean(logz - logits[np.arange(len(targets)), targets]))


def rms(r, gamma, epsilon):
    scale = np.sqrt(np.mean(r * r, axis=1, keepdims=True) + epsilon)
    return gamma * r / scale, scale


def pullback(p, r, hidden_cotangent):
    """Chain a supplied fixed hidden cotangent through RMS and both factors.

    q=A V^T; r=base+q U^T; h=gamma*r/s,
    gr=(gh*gamma)/s-r*sum(gh*gamma*r)/(hidden*s^3).
    gU=gr^T q and gV=(gr U)^T A.
    """
    _, scale = rms(r, p["gamma"], p["epsilon"])
    weighted = hidden_cotangent * p["gamma"]
    radial = np.sum(weighted * r, axis=1, keepdims=True)
    gr = weighted / scale - r * radial / (r.shape[1] * scale**3)
    q = p["a"] @ p["v"].T
    return {
        "hidden": hidden_cotangent,
        "r": gr,
        "u": gr.T @ q,
        "v": (gr @ p["u"]).T @ p["a"],
    }


def evaluate(p):
    q = p["a"] @ p["v"].T
    r = p["base"] + q @ p["u"].T
    h, _ = rms(r, p["gamma"], p["epsilon"])
    logits = h @ p["w"].T
    delta = probabilities(logits)
    delta[np.arange(len(p["targets"])), p["targets"]] -= 1
    delta /= len(p["targets"])
    gradients = pullback(p, r, delta @ p["w"])
    return {"r": r, "h": h, "logits": logits, "loss": ce(logits, p["targets"]),
            "delta": delta, "gradients": gradients}


def normalized_direction(rng, shape):
    x = rng.normal(size=shape)
    return x / np.linalg.norm(x)


def directional_checks(p, *, cotangent=None, label="decoded_linear_CE"):
    """F64 central differences of differentiable reference objectives only."""
    value = evaluate(p)
    rng = np.random.default_rng(194007)
    grads = value["gradients"] if cotangent is None else pullback(p, value["r"], cotangent @ p["w"])

    def loss_from_h(h):
        z = h @ p["w"].T
        return ce(z, p["targets"]) if cotangent is None else float(np.sum(z * cotangent))

    def loss_from_r(r):
        return loss_from_h(rms(r, p["gamma"], p["epsilon"])[0])

    def loss_from_factors(u, v):
        return loss_from_r(p["base"] + (p["a"] @ v.T) @ u.T)

    dh = normalized_direction(rng, value["h"].shape)
    dr = normalized_direction(rng, value["r"].shape)
    du = normalized_direction(rng, p["u"].shape)
    dv = normalized_direction(rng, p["v"].shape)
    cases = [
        ("hidden", lambda step: loss_from_h(value["h"] + step * dh), float(np.sum(grads["hidden"] * dh))),
        ("r", lambda step: loss_from_r(value["r"] + step * dr), float(np.sum(grads["r"] * dr))),
        ("u", lambda step: loss_from_factors(p["u"] + step * du, p["v"]), float(np.sum(grads["u"] * du))),
        ("v", lambda step: loss_from_factors(p["u"], p["v"] + step * dv), float(np.sum(grads["v"] * dv))),
        ("combined_uv", lambda step: loss_from_factors(p["u"] + step * du, p["v"] + step * dv),
         float(np.sum(grads["u"] * du) + np.sum(grads["v"] * dv))),
    ]
    reports = []
    for name, function, analytic in cases:
        for step in (1e-3, 1e-4, 1e-5):
            numerical = (function(step) - function(-step)) / (2 * step)
            error = abs(numerical - analytic)
            tolerance = max(5e-9, 2e-2 * step**2) * max(1.0, abs(analytic))
            if not np.isfinite(numerical) or error > tolerance:
                raise AssertionError(f"{label}/{name} FD failed: {error} > {tolerance}")
            reports.append({"objective": label, "parameter": name, "step": step,
                            "analytic": analytic, "central_difference": numerical,
                            "absolute_error": error, "tolerance": tolerance})
    return reports


def synthetic_document():
    rng = np.random.default_rng(820619)
    batch, hidden, vocab, din, rank = 3, 256, 17, 7, 2
    # Grid-valued synthetic decoded weights only: this is NOT a Q4_K encoder.
    f32 = lambda x: np.asarray(x, dtype=np.float32).astype(np.float64).tolist()
    return {"schema": SCHEMA, "epsilon": EPS, "fixtures": {
        "head_decoded_f32": f32(np.round(rng.normal(scale=.12, size=(vocab, hidden)) * 32) / 32),
        "base_r_f32": f32(rng.normal(scale=.6, size=(batch, hidden))),
        "gamma_f32": f32(rng.uniform(.7, 1.3, size=hidden)),
        "a_f32": f32(rng.normal(scale=.4, size=(batch, din))),
        "u_f32": f32(rng.normal(scale=.05, size=(hidden, rank))),
        "v_f32": f32(rng.normal(scale=.1, size=(rank, din))),
        "target_ids": [1, 8, 15],
    }}


def self_test():
    p = prepare(synthetic_document())
    value = evaluate(p)
    positive = directional_checks(p)
    fixed_delta = value["delta"] + .002  # Arbitrary fixed cotangent, not CE labels.
    positive += directional_checks(p, cotangent=fixed_delta, label="fixed_cotangent_linear_pullback")
    # A radial direction exposes omission of RMSNorm's coupling term.
    direction = value["r"] / np.linalg.norm(value["r"])
    _, scale = rms(value["r"], p["gamma"], p["epsilon"])
    wrong = value["gradients"]["hidden"] * p["gamma"] / scale
    correct = float(np.sum(value["gradients"]["r"] * direction))
    bad = float(np.sum(wrong * direction))
    threshold = 1e-5
    if abs(bad - correct) <= threshold:
        raise AssertionError("Missing-RMS-radial-term negative control was not rejected")
    negative = [{"name": "omit_RMS_radial_term", "status": "WRONG_GRADIENT_REJECTED",
                 "directional_discrepancy": abs(bad - correct), "minimum_discrepancy": threshold}]
    udir = value["gradients"]["u"] / np.linalg.norm(value["gradients"]["u"])
    exact = float(np.sum(value["gradients"]["u"] * udir))
    missing_mean = exact * len(p["targets"])
    if abs(missing_mean - exact) <= threshold:
        raise AssertionError("Missing-mean-reduction negative control was not rejected")
    negative.append({"name": "omit_batch_mean_reduction", "status": "WRONG_GRADIENT_REJECTED",
                     "directional_discrepancy": abs(missing_mean - exact), "minimum_discrepancy": threshold})
    return {"status": "PASS_PURE_REFERENCE_ONLY", "fixture_dimensions": {"hidden": 256, "vocab": 17,
            "batch": 3, "rank": 2, "din": 7}, "directional_checks": positive,
            "negative_controls": negative,
            "native_quantizer_run": False, "Q4_K_encoding_verified": False}


def compare_native(document):
    p = prepare(document)
    value = evaluate(p)
    n = document["native"]
    logits = array(n["cpu_logits"], "native.cpu_logits", value["logits"].shape)
    hidden = array(n["out_prod_hidden_gradient"], "native.out_prod_hidden_gradient", value["h"].shape)
    delta = probabilities(logits)
    delta[np.arange(len(p["targets"])), p["targets"]] -= 1
    delta /= len(p["targets"])
    expected = pullback(p, value["r"], delta @ p["w"])
    comparisons = []
    for native_key, gradient_key in (("out_prod_hidden_gradient", "hidden"),
                                     ("analytic_r_gradient", "r"),
                                     ("u_gradient", "u"), ("v_gradient", "v")):
        if native_key not in n:
            continue
        actual = array(n[native_key], "native." + native_key, expected[gradient_key].shape)
        wanted = expected[gradient_key]
        limit = NATIVE_ATOL + NATIVE_RTOL * np.abs(wanted)
        error = np.abs(actual - wanted)
        if np.any(error > limit):
            raise AssertionError(f"Native decoded pullback comparison failed: {native_key}")
        comparisons.append({"field": native_key, "status": "PASS", "max_abs_error": float(error.max()),
                            "absolute_tolerance": NATIVE_ATOL, "relative_tolerance": NATIVE_RTOL})
    checks = directional_checks(p)
    checks += directional_checks(p, cotangent=delta, label="fixed_native_CE_cotangent_decoded_pullback")
    return {"status": "PASS_NATIVE_FIXTURE_DECODED_PULLBACK_CHECKS", "comparisons": comparisons,
            "directional_checks": checks,
            "decoded_linear_mean_CE": value["loss"], "native_CPU_mean_CE": ce(logits, p["targets"]),
            "CPU_quantized_vs_decoded_logits_max_abs_difference": float(np.max(np.abs(logits - value["logits"]))),
            "native_forward_finite_differences_as_reported": n.get("quantized_forward_finite_differences"),
            "quantized_forward_FD_is_diagnostic_only": True,
            "exact_native_quantizer_gradient_claim": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-json", type=Path, help="Tiny synthetic native-probe JSON only")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--receipt", type=Path, help="Write a new receipt, failing if the path exists")
    args = parser.parse_args()
    report = {"schema": "synthetic-gradient-reference-verification-v1",
              "reference_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "runtime": {"python": platform.python_version(), "numpy": np.__version__},
              "limitations": ["Tiny synthetic fixtures only; no model data or model-quality evidence",
                  "Decoded-linear or fixed-cotangent surrogate gradients, not differentiation of native Q8_K activation quantization",
                  "No Metal/full-model equivalence or sequence-training benefit established"]}
    if args.self_test or args.native_json is None:
        report["self_test"] = self_test()
    if args.native_json is not None:
        raw = args.native_json.read_bytes()
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("Synthetic JSON exceeds 1MiB bound")
        report["native_input_sha256"] = hashlib.sha256(raw).hexdigest()
        report["native_check"] = compare_native(json.loads(raw))
        report["native_evidence_status"] = "NATIVE_FIXTURE_CHECKED_SURROGATE_ONLY"
    else:
        report["native_evidence_status"] = "UNRUN_NATIVE"
    if args.receipt:
        with args.receipt.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, allow_nan=False); stream.write("\n")
        print(json.dumps({"receipt": str(args.receipt), "sha256": hashlib.sha256(args.receipt.read_bytes()).hexdigest(),
                          "native_evidence_status": report["native_evidence_status"]}))
    else:
        print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
