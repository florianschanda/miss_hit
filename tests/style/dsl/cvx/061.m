cvx_begin
    variable A(n,n) symmetric
    variable b(n)
    maximize(det_rootn(A))
    subject to
        norms(A * x + b * ones(1, m), 2) <= 1;
cvx_end
