cvx_begin quiet
    variable x(n)
    minimize(norm(A * x - b, 1) + gamma(k) * norm(x, Inf))
cvx_end
