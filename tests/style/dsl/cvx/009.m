cvx_begin sdp
    variable Z(n,n) hermitian toeplitz
    dual variable Q
    minimize(norm(Z - P, 'fro'))
    Z >= 0:Q;
cvx_end
