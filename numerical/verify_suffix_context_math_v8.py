"""Synthetic F64 finite differences, key orthogonality, and bounded API checks."""
import argparse
import json
from pathlib import Path
import numpy as np
import suffix_context_math_v8 as sm


def verify():
    rng = np.random.default_rng(828031)
    r = rng.normal(size=7); gamma = .5 + rng.random(7)
    w = rng.normal(size=(2, 7)); eps = 1e-6
    expected_h = gamma * r / np.sqrt(np.sum(r*r)/7 + eps)
    np.testing.assert_allclose(sm.rms_hidden(r, gamma, eps), expected_h, rtol=1e-14)
    np.testing.assert_allclose(sm.selected_logits(r, gamma, eps, w), w @ expected_h, rtol=1e-14)
    grad = sm.pair_logit_gradient(r, gamma, eps, *w)
    fd = np.empty(7); step = 1e-6
    for j in range(7):
        direction = np.eye(7)[j]
        plus = sm.selected_logits(r + step*direction, gamma, eps, w)
        minus = sm.selected_logits(r - step*direction, gamma, eps, w)
        fd[j] = ((plus[0]-plus[1])-(minus[0]-minus[1]))/(2*step)
    np.testing.assert_allclose(grad, fd, atol=1e-8, rtol=1e-7)
    direction = rng.normal(size=7)
    plus = sm.selected_logits(r+step*direction, gamma, eps, w)
    minus = sm.selected_logits(r-step*direction, gamma, eps, w)
    directional_fd = ((plus[0]-plus[1])-(minus[0]-minus[1]))/(2*step)
    np.testing.assert_allclose(grad @ direction, directional_fd, atol=1e-8, rtol=1e-7)
    calibration = sm.calibrate_suffix(r, gamma, eps, w, expected_h, w @ expected_h)
    assert calibration['calibration_pass']
    failed_calibration = sm.calibrate_suffix(r, gamma, eps, w, expected_h, w @ expected_h + .001)
    assert not failed_calibration['calibration_pass']

    axes = np.eye(4)
    a = axes[0] + 2*axes[2]
    A = np.stack((axes[0], 3*axes[1], -2*axes[0]))
    key = sm.project_context_key(a, A)
    assert key.diagnostics['valid_key'] and key.diagnostics['guard_rank'] == 2
    np.testing.assert_allclose(key.v, .5*axes[2], atol=1e-12)
    np.testing.assert_allclose(A @ key.v, 0, atol=1e-12)
    assert abs(a @ key.v - 1) <= 1e-12
    no_guards = sm.project_context_key(a, np.empty((0, 4)))
    np.testing.assert_allclose(no_guards.v, a/(a@a), atol=1e-12)
    no_key = sm.project_context_key(a, np.vstack((A, a)))
    assert no_key.v is None and not no_key.diagnostics['valid_key']
    tiny = sm.project_context_key(axes[0]+1e-5*axes[2], axes[:1])
    assert tiny.v is None and tiny.diagnostics['separation_ratio'] < sm.MIN_SEPARATION_RATIO

    r2, g2 = np.array([1., 0.]), np.ones(2)
    wp, wm = np.array([0., 1.]), np.zeros(2)
    solved = sm.solve_pair_residual_step(r2, g2, eps, wp, wm, target_margin=.5, max_residual_l2=1)
    expected_tau = np.sqrt((1+2*eps)/7)
    np.testing.assert_allclose(solved.u, [0, expected_tau], atol=1e-12)
    assert solved.diagnostics['target_reached'] and solved.diagnostics['residual_cap_pass']
    capped = sm.solve_pair_residual_step(r2, g2, eps, wp, wm, target_margin=.5, max_residual_l2=.1)
    assert not capped.diagnostics['target_reached'] and capped.diagnostics['residual_cap_pass']
    assert np.linalg.norm(capped.u) <= .1
    already = sm.solve_pair_residual_step(r2, g2, eps, wp, wm, target_margin=-1, max_residual_l2=1)
    assert not already.u.any() and already.diagnostics['stop_reason'] == 'target_already_met'
    peak = sm.solve_pair_residual_step(r2, g2, eps, np.ones(2), wm, target_margin=2.1, max_residual_l2=10)
    assert not peak.diagnostics['target_reached']
    np.testing.assert_allclose(peak.diagnostics['exact_line_peak_tau'], 1+2*eps, atol=1e-12)
    assert peak.diagnostics['exact_line_peak_margin'] > 1.99
    nll = sm.nll_from_full_vocab_logz([2., 3.], [1., 2.5])
    np.testing.assert_allclose(nll['per_token_nll'], [1, .5])

    rejected = []
    def bad(label, action):
        try:
            action()
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError('Invalid input accepted: '+label)
    bad('zero_epsilon', lambda: sm.rms_hidden(r,gamma,0))
    bad('nonfinite_r', lambda: sm.rms_hidden(np.full(7,np.nan),gamma,eps))
    bad('complex_weights', lambda: sm.selected_logits(r,gamma,eps,w.astype(complex)))
    bad('negative_cap', lambda: sm.solve_pair_residual_step(r,gamma,eps,*w,target_margin=2,max_residual_l2=-1))
    bad('false_logz', lambda: sm.nll_from_full_vocab_logz([1.], [2.]))
    huge_v = np.broadcast_to(np.array(0.), (10_000_000,))
    huge_A = np.broadcast_to(np.array(0.), (10_000_000, 4))
    huge_W = np.broadcast_to(np.array(0.), (10_000_000, 7))
    class Bomb:
        def __array__(self,*a,**k):
            raise AssertionError('Arbitrary array protocol invoked')
    originals=np.asarray,np.isfinite
    def forbidden(*a,**k):
        raise AssertionError('Orphan input reached conversion/finite scan')
    try:
        np.asarray=np.isfinite=forbidden
        bad('oversized_r', lambda: sm.rms_hidden(huge_v,huge_v,eps))
        bad('oversized_gamma', lambda: sm.rms_hidden(r,huge_v,eps))
        bad('oversized_selected', lambda: sm.selected_logits(r,gamma,eps,huge_W))
        bad('oversized_key_guard', lambda: sm.project_context_key(a,huge_A))
        bad('arbitrary_protocol', lambda: sm.project_context_key(Bomb(),A))
        bad('overflow_epsilon', lambda: sm.rms_hidden(r,gamma,10**400))
    finally:
        np.asarray,np.isfinite=originals
    return dict(verification='passed',synthetic_only=True,numpy_version=np.__version__,
                checks=['rms_closed_form','all_coordinate_pair_gradient_finite_difference',
                        'directional_jvp_finite_difference','native_calibration_pass_and_fail_plumbing',
                        'known_context_projection','duplicate_guard_rank','recomputed_guard_orthogonality',
                        'normalized_positive_response','empty_guards','in_span_no_key','tiny_separation_rejected',
                        'known_exact_residual_step','residual_cap_failure','already_met_zero_step',
                        'interior_line_peak','full_vocab_logz_nll'],
                invalid_inputs_rejected=rejected,max_gradient_fd_error=float(np.max(np.abs(grad-fd))),
                directional_fd_error=float(abs(grad@direction-directional_fd)),
                key=key.diagnostics,tiny_separation=tiny.diagnostics,residual_step=solved.diagnostics,
                residual_cap_failure=capped.diagnostics,interior_peak=peak.diagnostics,
                native_calibration_is_still_required=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',type=Path)
    args=parser.parse_args();result=verify()
    if args.receipt:
        args.receipt.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(verification=result['verification'],checks=len(result['checks']),
                         invalid_inputs=len(result['invalid_inputs_rejected']),
                         max_gradient_fd_error=result['max_gradient_fd_error'])))
