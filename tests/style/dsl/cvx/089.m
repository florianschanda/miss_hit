cvx_begin
    variable P(n,n) symmetric
    minimize(norm(P - (1 / n) * ones(n)))
    P * ones(n, 1) == ones(n, 1);
    P >= 0;
    P(E == 0) == 0;
cvx_end
