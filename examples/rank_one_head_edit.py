"""A complete toy direct-weight edit using NumPy and the Python standard library.

Run from the project directory:
    python examples/rank_one_head_edit.py --output-dir demo-output

The output directory must be new. Omit --output-dir for a fresh temporary folder.
This creates a tiny checkpoint locally; it never reads or edits a real LLM.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import stat
import tempfile
import zipfile

import numpy as np

TOKENS = ("POSITIVE", "NEGATIVE", "OTHER")
WIDTH = 4
TARGET_MARGIN = 1.0


def _check(condition, message):
    if not condition:
        raise ValueError(message)


def _numeric(array, shape, name):
    _check(type(array) is np.ndarray and array.shape == shape and array.dtype.kind in "iuf",
           f"{name} must be a numeric ndarray with shape {shape}")
    result = np.asarray(array, dtype=np.float64)
    _check(np.isfinite(result).all(), f"{name} must be finite")
    return result


def fixture():
    """Fixed binary-exact numbers: no downloaded weights or random training."""
    weights = np.array([
        [-0.5, 0.125, -0.25, 0.25],
        [0.5, -0.125, 0.25, -0.25],
        [-1.0, -0.5, -0.5, 0.0],
    ], dtype=np.float32)
    target = np.array([1., 1., 0., 0.])
    guards = np.array([[0., 1., 0., 0.], [0., 0., 1., 0.]])
    return weights, target, guards


def fit_rank_one(weights, target, guards, *, target_margin=TARGET_MARGIN):
    """Fit an intended pair-margin request orthogonal to supplied guards.

    W has shape [tokens,features], so logits = W @ h. Project the target away
    from the guard row span, then normalize v so v @ target = 1. Choose u to
    raise POSITIVE and lower NEGATIVE equally. The direct update is u[:,None]
    @ v[None,:]. Guard protection is an algebraic statement about that intended
    update. F32 rounding can change it; run() checks the actual saved candidate.
    """
    W = _numeric(weights, (len(TOKENS), WIDTH), "weights")
    h = _numeric(target, (WIDTH,), "target")
    _check(type(guards) is np.ndarray and guards.ndim == 2 and guards.shape[1] == WIDTH
           and 0 <= len(guards) <= 8, "guards must have 0..8 rows and four features")
    G = _numeric(guards, (len(guards), WIDTH), "guards")
    _check(type(target_margin) in (int, float) and math.isfinite(target_margin), "target_margin must be finite")
    if len(G):
        _, singular, vt = np.linalg.svd(G, full_matrices=False)
        tolerance = np.finfo(float).eps * max(G.shape) * singular[0]
        basis = vt[singular > tolerance]
        separated = h - (h @ basis.T) @ basis
    else:
        separated = h.copy()
    _check(np.linalg.norm(separated) > 1e-12 * max(1., np.linalg.norm(h)),
           "The target cannot be separated robustly from these guards")
    v = separated / float(h @ separated)
    before_margin = float((W[0] - W[1]) @ h)
    increase = max(0., float(target_margin) - before_margin)
    u = np.array([increase / 2, -increase / 2, 0.])
    intended_delta = np.outer(u, v)
    candidate = (W + intended_delta).astype(np.float32)
    _check(np.isfinite(candidate).all(), "The candidate is not finite F32")
    return {"candidate": candidate, "u": u, "v": v, "intended_delta": intended_delta,
            "before_pair_margin": before_margin, "requested_pair_margin": float(target_margin)}


def sha256_file(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def save_new_checkpoint(path, weights):
    """Write a deterministic tiny NPZ exclusively; an existing path is rejected.

    Fixed ZIP timestamps/member order make identical arrays produce identical
    checkpoint hashes. Pickle is never used. This is a teaching NPZ, not GGUF.
    """
    _numeric(weights, (len(TOKENS), WIDTH), "weights")
    _check(weights.dtype == np.float32, "Serialized toy weights must already be F32")
    arrays = (("format_version", np.array(1, dtype=np.int64)), ("weights", weights))
    with Path(path).open("xb") as handle:
        with zipfile.ZipFile(handle, mode="w", compression=zipfile.ZIP_STORED) as archive:
            for name, array in arrays:
                buffer = io.BytesIO()
                np.lib.format.write_array(buffer, array, allow_pickle=False)
                member = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
                member.create_system = 3
                member.external_attr = 0o100644 << 16
                archive.writestr(member, buffer.getvalue())


def load_checkpoint(path):
    """Load only this example's small, known NPZ format without pickle."""
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        _check(len(members) == 2 and {m.filename for m in members} == {"format_version.npy", "weights.npy"}
               and all(m.file_size <= 4096 for m in members), "Unexpected or oversized toy checkpoint")
    with np.load(path, allow_pickle=False) as checkpoint:
        _check(checkpoint["format_version"].shape == () and int(checkpoint["format_version"]) == 1,
               "Unsupported toy checkpoint version")
        W = checkpoint["weights"].copy()
    _numeric(W, (len(TOKENS), WIDTH), "loaded weights")
    _check(W.dtype == np.float32, "Loaded weights must be F32")
    return W


def describe_context(weights, hidden, expected):
    logits = weights.astype(np.float64) @ hidden
    winner = int(np.argmax(logits))
    remaining = np.delete(logits, expected)
    return {"logits": logits.tolist(), "winner": TOKENS[winner],
            "expected": TOKENS[expected], "correct": winner == expected,
            "expected_margin_over_all_others": float(logits[expected] - np.max(remaining))}


def separate_evaluation(parent, candidate):
    """These deliberately chosen labels/contexts do not enter fit_rank_one.

    The same edit helps one new context and harms another that shares the edited
    feature. This is a limits demonstration, not a statistical benchmark.
    """
    contexts = (
        ("near_target", np.array([1., 0., 0., 0.]), 0),
        ("unprotected_shared_feature", np.array([1., 3., 0., 0.]), 1),
        ("orthogonal_unseen", np.array([0., 0., 0., 1.]), 0),
    )
    rows = []
    for name, hidden, label in contexts:
        before, after = describe_context(parent, hidden, label), describe_context(candidate, hidden, label)
        outcome = "improved" if not before["correct"] and after["correct"] else (
            "regressed" if before["correct"] and not after["correct"] else "unchanged_correctness")
        rows.append({"name": name, "hidden": hidden.tolist(), "before": before, "after": after, "outcome": outcome})
    return {"used_for_fitting": False, "deliberately_engineered_limits_demo": True, "contexts": rows,
            "parent_correct": sum(row["before"]["correct"] for row in rows),
            "candidate_correct": sum(row["after"]["correct"] for row in rows), "total": len(rows)}


def toy_rounding_demo():
    """A scalar uniform grid, explicitly NOT a real LLM quantization format."""
    parent, intended, step = 0.5, 0.001, 0.1
    control = float(np.round(parent / step) * step)
    edited = float(np.round((parent + intended) / step) * step)
    return {"toy_uniform_scalar_grid_only": True, "real_LLM_codec": False,
            "grid_step": step, "intended_delta": intended,
            "stored_edited_minus_control": edited - control, "edit_erased": edited == control}


def run(output_dir=None):
    """Create fresh artifacts, reload them, and verify actual stored effects."""
    if output_dir is None:
        destination = Path(tempfile.mkdtemp(prefix="weight-edit-toy-"))
    else:
        destination = Path(output_dir).expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=False)
    parent_path, candidate_path = destination / "parent.npz", destination / "candidate.npz"
    weights, target, guards = fixture()
    save_new_checkpoint(parent_path, weights)
    parent_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    parent_hash_before = sha256_file(parent_path)
    parent = load_checkpoint(parent_path)
    fit = fit_rank_one(parent, target, guards)
    save_new_checkpoint(candidate_path, fit["candidate"])
    candidate = load_checkpoint(candidate_path)
    actual_delta = candidate.astype(np.float64) - parent.astype(np.float64)
    parent_hash_after = sha256_file(parent_path)
    before_target = describe_context(parent, target, 0)
    after_target = describe_context(candidate, target, 0)
    guard_before = guards @ parent.astype(np.float64).T
    guard_after = guards @ candidate.astype(np.float64).T
    guard_drift = float(np.max(np.abs(guard_after - guard_before)))
    _check(parent_hash_before == parent_hash_after, "Parent checkpoint changed")
    _check(parent.tobytes() == weights.tobytes(), "Loaded parent differs from fixture")
    _check(candidate.tobytes() == fit["candidate"].tobytes(), "Serialized candidate differs from intended F32 array")
    _check(guard_drift == 0., "A protected guard logit changed")
    _check(after_target["expected_margin_over_all_others"] >= TARGET_MARGIN, "Stored candidate missed the target margin")
    receipt = {
        "schema": "toy-rank-one-output-head-edit-v1", "toy_only": True, "real_model_edited": False,
        "checkpoint_generation": "fixed locally generated dyadic F32 fixture; no downloads or training corpus",
        "numpy_version": np.__version__, "tokens": list(TOKENS), "weight_shape_tokens_features": [3, 4],
        "artifacts": {
            "parent": {"file": "parent.npz", "sha256": parent_hash_before, "read_only_requested": True},
            "candidate": {"file": "candidate.npz", "sha256": sha256_file(candidate_path)},
        },
        "parent_sha256_after": parent_hash_after, "parent_unchanged": parent_hash_before == parent_hash_after,
        "edit": {"formula": "W_candidate = F32(W_parent + u[:,None] @ v[None,:])",
                 "u_tokens": fit["u"].tolist(), "v_features": fit["v"].tolist(),
                 "target_key_response": float(target @ fit["v"]), "guard_key_responses": (guards @ fit["v"]).tolist(),
                 "intended_delta": fit["intended_delta"].tolist(), "actual_reloaded_delta": actual_delta.tolist(),
                 "intended_delta_frobenius": float(np.linalg.norm(fit["intended_delta"])),
                 "actual_delta_frobenius": float(np.linalg.norm(actual_delta)),
                 "intended_vs_actual_error_frobenius": float(np.linalg.norm(actual_delta - fit["intended_delta"])),
                 "changed_weights": int(np.count_nonzero(actual_delta)), "serialized_candidate_bit_exact": True},
        "target": {"hidden": target.tolist(), "requested_margin": TARGET_MARGIN,
                   "before": before_target, "after": after_target},
        "guards": {"hidden_rows": guards.tolist(), "before_logits": guard_before.tolist(),
                   "after_logits": guard_after.tolist(), "maximum_absolute_logit_drift": guard_drift,
                   "all_supplied_guard_logits_unchanged": guard_drift == 0.},
        "separate_evaluation": separate_evaluation(parent, candidate), "toy_rounding": toy_rounding_demo(),
        "limitations": ["Only three toy tokens and four supplied features; no transformer or tokenizer.",
                        "Only supplied guard directions are protected; an unprotected context regresses.",
                        "Selected examples demonstrate algebra and limits, not broad model improvement.",
                        "The toy scalar grid is not a real LLM quantization codec."]}
    with (destination / "receipt.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return destination, receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="New directory only; omitted means a fresh temporary directory")
    args = parser.parse_args()
    try:
        folder, result = run(args.output_dir)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"Example stopped: {exc}\n")
    print(json.dumps({"output_directory": str(folder), "parent_unchanged": result["parent_unchanged"],
                      "target_margin_before": result["target"]["before"]["expected_margin_over_all_others"],
                      "target_margin_after": result["target"]["after"]["expected_margin_over_all_others"],
                      "protected_guard_max_logit_drift": result["guards"]["maximum_absolute_logit_drift"],
                      "evaluation_outcomes": [row["outcome"] for row in result["separate_evaluation"]["contexts"]],
                      "receipt": "receipt.json"}))
