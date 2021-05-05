cvx_begin
    variable x(n)
    minimize(sum(max(abs(A * x - b) - 1, 0)))
cvx_end
