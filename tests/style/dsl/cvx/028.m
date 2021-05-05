cvx_begin sdp
    variable nu(n)
    maximize (-sum(nu))
    W + diag(nu) >= 0;
cvx_end
cvx_begin sdp
    variable X(n,n) symmetric
    minimize (trace(W * X))
    diag(X) == 1;
    X >= 0;
cvx_end
