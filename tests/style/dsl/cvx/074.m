cvx_begin quiet
    variable x1(n)
    minimize (norm(A * x1 - v', inf))
cvx_end
