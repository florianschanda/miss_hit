cvx_begin
    variable x(n)
    minimize(sum(max(A * x - b, 0)))
cvx_end
