cvx_begin quiet
    variable x(n)
    minimize (norm(x - x0))
    x <= u;
    x >= l;
cvx_end
