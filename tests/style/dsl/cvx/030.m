cvx_begin quiet
    variable x(n)
    minimize (norm (A * x - b, p))
cvx_end
cvx_begin quiet
    variables x(n) y(m)
    minimize (norm (y, p))
    A * x - b == y;
cvx_end
cvx_begin quiet
    variable nu(m)
    maximize (b' * nu)
    norm(nu, q) <= 1;
    A' * nu == 0;
cvx_end
cvx_begin quiet
    variables x(n) y(m)
    minimize (0.5 * square_pos (norm (y, p)))
    A * x - b == y;
cvx_end
cvx_begin quiet
    variable nu(m)
    maximize (-0.5 * square_pos (norm (nu, q)) + b' * nu)
    A' * nu == 0;
cvx_end
