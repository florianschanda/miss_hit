cvx_begin sdp
    variable w(m,1)   % edge weights
    variable s        % epigraph variable
    variable L(n,n) symmetric
    minimize(s)
    subject to
        L == A * diag(w) * A';
        -s * I <= J - L <= +s * I;
        w >= 0;
        diag(L) <= 1;
cvx_end
