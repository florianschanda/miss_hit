cvx_begin quiet
    variable xs0(n)
    minimize (square_pos(norm(xs0 - x0)))
    a' * xs0 <= b;
cvx_end
cvx_begin quiet
    variable xs1(n)
    minimize (square_pos(norm(xs1 - x1)))
    a' * xs1 <= b;
cvx_end
