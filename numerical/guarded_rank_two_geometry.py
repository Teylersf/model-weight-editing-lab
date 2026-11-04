"""Guard projection used by the saved Windows rank-two experiment."""

import time

import numpy as np
from scipy.linalg.lapack import dgeqp3, dormqr


def require(condition,message):
    if not condition:
        raise ValueError(message)


def apply_q(reflectors,tau,matrix,transpose):
    direction = b"T" if transpose else b"N"
    _,work,info = dormqr(b"L",direction,reflectors,tau,matrix,-1,overwrite_c=0)
    require(info==0 and np.isfinite(work[0]),"LAPACK implicit Q workspace query failed")
    answer,_,info = dormqr(b"L",direction,reflectors,tau,matrix,int(work[0]),overwrite_c=0)
    require(info==0,"LAPACK implicit Q application failed")
    return answer


def guard_chunks(blocks):
    for group in blocks:
        for start in range(0,len(group),256):
            yield np.asarray(group[start:start+256],dtype=np.float64)


def geometry(blocks,positive,progress=lambda **_:None):
    """Use all exact guard columns in pivoted QR and avoid materializing a dense Q."""
    a = np.asarray(positive,dtype=np.float64)
    require(a.ndim==2 and len(a) in (1,2) and np.isfinite(a).all(),"Invalid exact positive matrix")
    width = a.shape[1]
    n = sum(map(len,blocks))
    require(0<n<width and all(group.ndim==2 and group.shape[1]==width for group in blocks),
            "Full guard transpose requires fewer guard rows than features")
    columns = np.empty((width,n),dtype=np.float64,order="F")
    offset = 0
    for block in guard_chunks(blocks):
        require(np.isfinite(block).all(),"Nonfinite exact guard activation")
        columns[:,offset:offset+len(block)] = block.T
        offset += len(block)
    _,_,_,query,info = dgeqp3(columns,lwork=-1,overwrite_a=1)
    require(info==0 and np.isfinite(query[0]),"Pivoted QR workspace query failed")
    start = time.perf_counter()
    progress(phase="pivoted_qr_start",features=width,guard_rows=n,transpose_bytes=columns.nbytes)
    reflectors,pivots,tau,_,info = dgeqp3(columns,lwork=int(query[0]),overwrite_a=1)
    require(info==0 and np.array_equal(np.sort(pivots),np.arange(1,n+1)),"Full pivoted QR failed")
    qr_seconds = time.perf_counter()-start
    progress(phase="pivoted_qr_complete",elapsed_seconds=qr_seconds)
    diagonal = np.abs(np.diag(reflectors))
    require(np.isfinite(diagonal).all() and len(diagonal)==n,"Invalid QR diagonal")
    tolerance = np.finfo(np.float64).eps*max(width,n)*diagonal[0]
    rank = int(np.count_nonzero(diagonal>tolerance))
    result = dict(algorithm="LAPACK DGEQP3 with implicit DORMQR, all guard rows",
                  feature_width=width,guard_rows=n,positive_rows=len(a),guard_rank=rank,
                  guard_rank_tolerance=float(tolerance),guard_R_pivot_diagonal_first=float(diagonal[0]),
                  guard_R_pivot_diagonal_last_retained=float(diagonal[rank-1]) if rank else None,
                  guard_R_pivot_diagonal_first_discarded=float(diagonal[rank]) if rank<n else None,
                  guard_R_pivot_diagonal_last_first_ratio=float(diagonal[rank-1]/diagonal[0]) if rank else None,
                  guard_diagonal_ratio_is_not_condition_number=True,
                  numerical_null_dimension=width-rank,qr_seconds=qr_seconds,
                  matrix_change_policy="report_only")
    if not np.all(diagonal[:rank]>tolerance) or width-rank<len(a):
        return None,dict(result,qualified=False,reason="PIVOTED_QR_NUMERICAL_RANK_UNQUALIFIED")
    if rank:
        householder = reflectors[:,:rank]
        coordinates = apply_q(householder,tau[:rank],np.asfortranarray(a.T),True)
        coordinates[:rank,:] = 0.
        projected = apply_q(householder,tau[:rank],coordinates,False).T
    else:
        projected = a.copy()
    original_norm = np.linalg.norm(a,axis=1)
    lengths = np.linalg.norm(projected,axis=1)
    ratios = np.divide(lengths,original_norm,out=np.zeros_like(lengths),where=original_norm>0)
    result.update(projected_positive_norms=lengths.tolist(),positive_separation_ratios=ratios.tolist())
    if not np.isfinite(ratios).all() or np.any(ratios<1e-3):
        return None,dict(result,qualified=False,reason="POSITIVE_SEPARATION_UNQUALIFIED")
    u,singular,vt = np.linalg.svd(projected/lengths[:,None],full_matrices=False)
    ratio = float(singular[-1]/singular[0])
    result.update(normalized_positive_singular_values=singular.tolist(),
                  normalized_positive_gram_condition=1/ratio**2 if ratio>1e-150 else None)
    if ratio<1e-3:
        return None,dict(result,qualified=False,reason="POSITIVE_GRAM_CONDITION_UNQUALIFIED")
    keys = ((vt.T/singular)@u.T)/lengths
    exact_positive = a@keys
    positive_error = float(np.max(np.abs(exact_positive-np.eye(len(a)))))
    key_norm = np.linalg.norm(keys,axis=0)
    max_guard = np.zeros(len(a))
    max_guard_relative = np.zeros(len(a))
    max_projected = np.zeros(len(a))
    for block in guard_chunks(blocks):
        response = np.abs(block@keys)
        row_norm = np.linalg.norm(block,axis=1)
        denom = row_norm[:,None]*key_norm
        relative = np.divide(response,denom,out=np.zeros_like(response),where=denom>0)
        max_guard = np.maximum(max_guard,np.max(response,axis=0))
        max_guard_relative = np.maximum(max_guard_relative,np.max(relative,axis=0))
        max_projected = np.maximum(max_projected,np.max(np.abs(block@projected.T),axis=0))
    result.update(maximum_positive_identity_error=positive_error,actual_positive_response=exact_positive.tolist(),
                  maximum_guard_response_by_key=max_guard.tolist(),
                  maximum_guard_relative_response_by_key=max_guard_relative.tolist(),
                  maximum_guard_dot_projected_positive=max_projected.tolist(),
                  key_l2_norms=key_norm.tolist(),key_metric=(keys.T@keys).tolist(),
                  guard_response_checked_over_exact_original_rows=True,
                  rounded_f32_storage_response_not_measured=True)
    if not np.isfinite(keys).all() or positive_error>1e-8 or np.max(max_guard)>1e-6:
        return None,dict(result,qualified=False,reason="RECOMPUTED_FULL_GUARD_RESPONSE_UNQUALIFIED")
    return keys,dict(result,qualified=True)
