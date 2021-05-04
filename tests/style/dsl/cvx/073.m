cvx_begin quiet
    variable x(n)
    minimize(norm(A * x - b))
    subject to
        norm(x, 1) <= alpha;
cvx_end
