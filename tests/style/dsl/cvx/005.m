cvx_begin
    variable x(n)
    minimize(norm(A * x - b))
cvx_end
