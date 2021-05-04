cvx_begin
    variable x(n)
    minimize(0.5 * sum_square(y - x) + lambda * norm(D * x, 1))
cvx_end
