"""Independent algebra and serialized-artifact checks; standard unittest runner."""
import hashlib
import tempfile
from pathlib import Path
import unittest

import numpy as np

from examples.rank_one_head_edit import (fixture, fit_rank_one, load_checkpoint, run,
                                        save_new_checkpoint, toy_rounding_demo)


class RankOneExampleTests(unittest.TestCase):
    def test_orientation_and_known_solution(self):
        parent, target, guards = fixture()
        fit = fit_rank_one(parent, target, guards)
        np.testing.assert_array_equal(fit["v"], [1., 0., 0., 0.])
        np.testing.assert_array_equal(fit["u"], [.875, -.875, 0.])
        expected = np.zeros((3, 4)); expected[0, 0], expected[1, 0] = .875, -.875
        np.testing.assert_array_equal(fit["intended_delta"], expected)
        # A second context independently tests matrix orientation W @ h.
        probe = np.array([2., -3., .5, 7.])
        np.testing.assert_array_equal(fit["intended_delta"] @ probe,
                                      fit["u"] * float(fit["v"] @ probe))
        np.testing.assert_array_equal(guards @ fit["v"], [0., 0.])

    def test_target_and_all_guard_logits(self):
        parent, target, guards = fixture()
        candidate = fit_rank_one(parent, target, guards)["candidate"]
        logits = candidate.astype(float) @ target
        self.assertEqual(int(np.argmax(logits)), 0)
        self.assertEqual(float(logits[0] - max(logits[1:])), 1.0)
        np.testing.assert_array_equal(guards @ candidate.astype(float).T, guards @ parent.astype(float).T)

    def test_actual_artifacts_reload_parent_hash_and_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            folder, receipt = run(Path(temp) / "fresh")
            parent = load_checkpoint(folder / "parent.npz")
            candidate = load_checkpoint(folder / "candidate.npz")
            actual = candidate.astype(float) - parent.astype(float)
            np.testing.assert_array_equal(actual, receipt["edit"]["actual_reloaded_delta"])
            self.assertTrue(receipt["edit"]["serialized_candidate_bit_exact"])
            self.assertEqual(hashlib.sha256((folder / "parent.npz").read_bytes()).hexdigest(),
                             receipt["artifacts"]["parent"]["sha256"])
            self.assertEqual(receipt["parent_sha256_after"], receipt["artifacts"]["parent"]["sha256"])
            self.assertEqual([r["outcome"] for r in receipt["separate_evaluation"]["contexts"]],
                             ["improved", "regressed", "unchanged_correctness"])
            self.assertEqual(receipt["separate_evaluation"]["parent_correct"], 2)
            self.assertEqual(receipt["separate_evaluation"]["candidate_correct"], 2)

    def test_checkpoint_bytes_are_deterministic_and_cannot_overwrite(self):
        parent, _, _ = fixture()
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / "a.npz", Path(temp) / "b.npz"
            save_new_checkpoint(a, parent); save_new_checkpoint(b, parent)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            original = a.read_bytes()
            with self.assertRaises(FileExistsError):
                save_new_checkpoint(a, parent + np.float32(1))
            self.assertEqual(a.read_bytes(), original)

    def test_existing_output_directory_is_never_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            sentinel = Path(temp) / "keep.txt"; sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                run(temp)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertEqual(sorted(p.name for p in Path(temp).iterdir()), ["keep.txt"])

    def test_target_in_guard_span_is_rejected(self):
        parent, target, _ = fixture()
        with self.assertRaisesRegex(ValueError, "cannot be separated"):
            fit_rank_one(parent, target, target[None, :])

    def test_rounding_demo_has_an_explicit_toy_label(self):
        result = toy_rounding_demo()
        self.assertTrue(result["toy_uniform_scalar_grid_only"])
        self.assertFalse(result["real_LLM_codec"])
        self.assertTrue(result["edit_erased"])
        self.assertEqual(result["stored_edited_minus_control"], 0.)


if __name__ == "__main__":
    unittest.main()
