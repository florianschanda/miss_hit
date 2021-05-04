cvx_begin
    variable u(n)
    minimize (max (P' * u))
    u >= 0;
    ones(1, n) * u == 1;
cvx_end
cvx_begin
    variable v(m)
    maximize (min (P * v))
    v >= 0;
    ones(1, m) * v == 1;
cvx_end
