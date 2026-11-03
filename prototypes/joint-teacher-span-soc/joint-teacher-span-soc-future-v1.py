"""Tiny NumPy-only formulation diagnostics; no optimizer/model/native/cache I/O.

All arrays are invented synthetic fixtures. Passing finite checks does not prove
convexity, native equivalence, feasibility of a real edit or model improvement.
The accompanying design supplies the conditional mathematical argument.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import numpy as np

if not __debug__:
    raise RuntimeError("Diagnostics require assertions enabled")


def sigma(s,epsilon):
    if epsilon<=0:raise ValueError("Positive fixed epsilon required")
    return float(np.sqrt(np.dot(s,s)/len(s)+epsilon))


def quantities(U,r,q,t,margin,epsilon):
    if margin<=0:raise ValueError("This SOC representation requires positive margin")
    s=r+U@q;scale=sigma(s,epsilon)
    normalized=float(t@s)/scale
    violation=margin*scale-float(t@s)
    lifted=np.append(s/np.sqrt(len(s)),np.sqrt(epsilon))
    soc_slack=float(t@s)/margin-float(np.linalg.norm(lifted))
    return s,normalized,violation,soc_slack


def gradients(U,r,q,t,margin,epsilon):
    s=r+U@q;scale=sigma(s,epsilon);d=len(s)
    normalized=np.outer(t/scale-s*float(t@s)/(d*scale**3),q)
    violation=np.outer(margin*s/(d*scale)-t,q)
    return normalized,violation


def fd(function,U,direction,step=1e-6):
    return (function(U+step*direction)-function(U-step*direction))/(2*step)


def run():
    rng=np.random.default_rng(20261103)
    records=[]
    def done(name,**details):records.append(dict(name=name,status="PASS_SYNTHETIC_DIAGNOSTIC",**details))
    worst_equivalence=worst_jensen=0.0
    # Random bounded checks support implementation consistency, not a proof.
    for i in range(64):
        d=2+i%6;k=1+i%4
        r=rng.normal(size=d);q=rng.normal(size=k);t=rng.normal(size=d)
        U=rng.normal(size=(d,k));V=rng.normal(size=(d,k));m=.2+(i%5)/10;eps=.03
        s,margin,violation,slack=quantities(U,r,q,t,m,eps)
        err=max(abs(violation+m*slack),abs((margin-m)*sigma(s,eps)+violation))
        worst_equivalence=max(worst_equivalence,err)
        assert err<2e-12
        weight=.37
        left=quantities(weight*U+(1-weight)*V,r,q,t,m,eps)[2]
        right=weight*violation+(1-weight)*quantities(V,r,q,t,m,eps)[2]
        worst_jensen=max(worst_jensen,left-right)
        assert left<=right+2e-12
    done("RMS_margin_SOC_algebra",finite_fixtures=64,max_abs_identity_error=worst_equivalence)
    done("convex_violation_Jensen_checks",finite_fixtures=64,max_Jensen_excess=worst_jensen,
         finite_sampling_is_not_convexity_proof=True)

    worst_norm=worst_violation=worst_adjoint=0.0
    for i in range(24):
        d,k=5,3;r=rng.normal(size=d);q=rng.normal(size=k);t=rng.normal(size=d)
        U=rng.normal(scale=.3,size=(d,k));direction=rng.normal(size=(d,k));direction/=np.linalg.norm(direction)
        m,eps=.6,.07
        gn,gv=gradients(U,r,q,t,m,eps)
        nfd=fd(lambda u:quantities(u,r,q,t,m,eps)[1],U,direction)
        vfd=fd(lambda u:quantities(u,r,q,t,m,eps)[2],U,direction)
        worst_norm=max(worst_norm,abs(nfd-float(np.sum(gn*direction))))
        worst_violation=max(worst_violation,abs(vfd-float(np.sum(gv*direction))))
        # Adjoint of the LINEAR part of (t.s/m, [s/sqrt(d),sqrt(eps)]).
        zeta=float(rng.normal());eta=rng.normal(size=d)
        shift=U@q
        left=zeta*float(t@shift)/m+float(eta@shift)/np.sqrt(d)
        adjoint=np.outer(zeta*t/m+eta/np.sqrt(d),q)
        worst_adjoint=max(worst_adjoint,abs(left-float(np.sum(U*adjoint))))
    assert max(worst_norm,worst_violation)<5e-8 and worst_adjoint<2e-12
    done("normalized_margin_gradient",directions=24,max_abs_FD_error=worst_norm)
    done("SOC_violation_gradient",directions=24,max_abs_FD_error=worst_violation)
    done("affine_SOC_linear_part_adjoint",fixtures=24,max_abs_error=worst_adjoint)

    G=np.array([[1.,0.,1.,0.,0.,0.],[0.,1.,0.,1.,0.,0.]])
    K=np.array([[1.,0.],[0.,1.],[-1.,0.],[0.,-1.],[0.,0.],[0.,0.]])/np.sqrt(2.)
    U=rng.normal(size=(4,2));delta=U@K.T
    leak=float(np.max(np.abs(delta@G.T)))
    orth_error=float(np.max(np.abs(K.T@K-np.eye(2))))
    assert leak<1e-13 and orth_error<1e-13
    assert abs(np.linalg.norm(delta)**2-np.linalg.norm(U)**2)<1e-12
    done("orthonormal_null_basis_guard_and_Frobenius",intended_guard_max_abs=leak,orthogonality_error=orth_error)

    K2=K@np.array([[1.,.4],[.2,1.3]])
    gram=K2.T@K2;actual=float(np.linalg.norm(U@K2.T)**2)
    formula=float(np.trace(U@gram@U.T));wrong=float(np.linalg.norm(U)**2)
    assert abs(actual-formula)<1e-12 and abs(actual-wrong)>1e-3
    direction=rng.normal(size=U.shape);direction/=np.linalg.norm(direction)
    # Gradient of half the actual matrix squared norm is U @ (K.T K).
    measured=fd(lambda u:.5*float(np.linalg.norm(u@K2.T)**2),U,direction)
    err=abs(measured-float(np.sum((U@gram)*direction)));assert err<5e-8
    done("nonorthogonal_basis_metric",identity_error=abs(actual-formula),gradient_FD_error=err,
         wrong_orthonormal_shortcut_rejected=True)

    prior=rng.normal(size=delta.shape)
    combined=float(np.linalg.norm(prior+delta)**2)
    expanded=float(np.linalg.norm(prior)**2+2*np.sum((prior@K)*U)+np.trace(U@(K.T@K)@U.T))
    assert abs(combined-expanded)<1e-11
    done("cumulative_matrix_drift_expansion",max_abs_error=abs(combined-expanded))

    r=np.zeros(2);q1=np.array([1.,0.]);q2=np.array([0.,1.]);t1=q1.copy();t2=q2.copy()
    first=2*np.eye(2);second=3*np.eye(2)
    for u in (first,second,.4*first+.6*second):
        assert quantities(u,r,q1,t1,.5,.1)[2]<=0 and quantities(u,r,q2,t2,.5,.1)[2]<=0
    done("joint_full_rank_feasible_example",positive_states=2,feasible_convex_mix=True)

    # Duplicate keys can be compatible; rank deficiency alone proves nothing.
    q=np.array([1.]);up=np.array([[1.],[0.]]);down=-up
    assert quantities(up,r,q,t1,.5,.1)[2]<0
    assert quantities(up,r,q,t1,.5,.1)[2]<0
    assert quantities(down,r,q,-t1,.5,.1)[2]<0
    # With identical r/q and opposite t, adding two positive-margin inequalities
    # would require 0 >= 2*m*sigma, an analytic contradiction since epsilon>0.
    independently_summed=up+down
    assert quantities(independently_summed,r,q,t1,.5,.1)[2]>0
    assert quantities(independently_summed,r,q,-t1,.5,.1)[2]>0
    done("duplicate_key_compatibility_and_opposed_contradiction",rank_deficiency_alone_is_not_infeasibility=True,
         independent_repairs_sum_rejected=True,contradiction_scope="Exact toy identical-r/q opposite-t positive-margin fixture only")

    zero=np.array([0.]);baseline=quantities(up,r,zero,t1,.5,.1)[2]
    assert baseline>0 and np.array_equal(up@zero,np.zeros(2))
    done("zero_key_uneditable_state",fixed_baseline_violation=baseline)

    stress=[]
    for small in (1e-1,1e-3,1e-5):
        Q=np.array([[1.,1.],[0.,small]])
        desired=np.eye(2);interpolant=np.linalg.solve(Q.T,desired.T).T
        assert np.max(np.abs(interpolant@Q-desired))<1e-10
        stress.append(dict(key_separation=small,condition=float(np.linalg.cond(Q)),required_interpolant_Frobenius=float(np.linalg.norm(interpolant))))
    assert all(stress[i+1]['required_interpolant_Frobenius']>90*stress[i]['required_interpolant_Frobenius'] for i in range(2))
    done("near_collinear_keys_linear_interpolation_stress",fixtures=stress,
         not_a_general_SOC_infeasibility_certificate=True)

    guard=np.array([1.,1.]);basis=np.array([[1.],[-1.]])/np.sqrt(2.)
    small_U=np.array([[9e-8*np.sqrt(2.)]])
    intended=small_U@basis.T;control=np.array([[1.,4.]],dtype=np.float32)
    stored=(control.astype(np.float64)+intended).astype(np.float32)
    actual=stored.astype(np.float64)-control.astype(np.float64)
    ideal_leak=float((intended@guard)[0]);stored_leak=float((actual@guard)[0])
    assert abs(ideal_leak)<1e-20 and abs(stored_leak)>1e-8
    done("F32_materialization_can_break_intended_guard_nullspace",intended_guard_response=ideal_leak,
         actual_stored_guard_response=stored_leak,actual_stored_delta=actual.tolist())

    return {'schema':'joint-teacher-span-SOC-synthetic-diagnostics-v1',
            'status':'PASS_FORMULATION_DIAGNOSTICS_NOT_OPTIMIZER_OR_MODEL_EVIDENCE',
            'runtime':{'python':platform.python_version(),'numpy':np.__version__},
            'groups':records,'group_count':len(records),
            'claims':{'convexity_proved_by_this_finite_script':False,'SOCP_solver_implemented':False,
                      'real_model_or_weight_data_used':False,'native_or_Mac_execution':False,
                      'teacher_prefix_reachability_established':False,'exact_solver_or_native_certificate':False,
                      'current_V11_method_changed':False},
            'limitations':['Tiny invented arrays only','Finite arithmetic checks support formula implementation, not a proof or a real-fit result',
                           'Near-collinear interpolation stress is not proof the margin problem is infeasible',
                           'F32 counterexample demonstrates possible leakage, not leakage of any actual candidate',
                           'Teacher features, native full-vocabulary scores, stored-weight checks and complete answers remain untested']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',type=Path,help='New diagnostic receipt; refuse overwrite')
    args=parser.parse_args();report=run()
    report['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.receipt:
        with args.receipt.open('x',encoding='utf-8',newline='\n') as out:
            json.dump(report,out,indent=2,allow_nan=False);out.write('\n')
    print(json.dumps({'status':report['status'],'diagnostic_groups':report['group_count'],
                      'source_sha256':report['source_sha256'],
                      'receipt_sha256':hashlib.sha256(args.receipt.read_bytes()).hexdigest() if args.receipt else None}))
