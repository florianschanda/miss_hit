cvx_begin
    variable x1(2)
    minimize (sum(norms(x1 * ones(1, K) - P, 1)))
cvx_end
cvx_begin
    variable x2(2)
    minimize (sum(norms(x2 * ones(1, K) - P, 2)))
cvx_end
