cvx_begin
    variables u(n) t1
    minimize (t1)
    u >= 0;
    ones(1, n) * u == 1;
    P' * u <= t1 * ones(m, 1);
cvx_end
cvx_begin
    variables v(m) t2
    maximize (t2)
    v >= 0;
    ones(1, m) * v == 1;
    P * v >= t2 * ones(n, 1);
cvx_end
