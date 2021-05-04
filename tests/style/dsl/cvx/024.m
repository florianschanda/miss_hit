cvx_begin
    variable x1(n)
    minimize (quad_form(x1, sig))
    p_mean' * x1 >= r_min;
    ones(1, n) * x1 == 1;
    x1 >= 0;
    sum_largest(x1, r) <= alpha;
cvx_end
cvx_begin
    variables x2(n) u(n) t(1)
    minimize (quad_form(x2, sig))
    p_mean' * x2 >= r_min;
    sum(x2) == 1;
    x2 >= 0;
    r * t + sum(u) <= alpha;
    t * ones(n, 1) + u >= x2;
    u >= 0;
cvx_end
