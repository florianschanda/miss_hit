cvx_begin quiet
    variable x(n)
    minimize (square_pos(norm(x - x0)))
    a' * x == b;
cvx_end
