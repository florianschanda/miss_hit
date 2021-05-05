cvx_begin quiet
    variable x(n)
    minimize(norm(x - corrupt) + lambda * norm(x(2:n) - x(1:n - 1)))
cvx_end
cvx_begin quiet
    variable x(n)
    minimize(norm(x(2:n) - x(1:n - 1)))
    subject to
        norm(x - corrupt) <= alpha;
cvx_end
