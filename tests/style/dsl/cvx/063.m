cvx_begin quiet
    variable u( m )
    minimize(b' * u + 0.5 * sum_square(chol(Sigma) * A' * u))
    subject to
        u >= 0;
cvx_end
