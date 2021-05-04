cvx_begin quiet
    variable x(n)
    minimize (norm(x - x0))
    x >= 0;
cvx_end
