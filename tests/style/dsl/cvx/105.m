cvx_begin
    variable h(n,1)
    minimize(max(abs(A * h - Hdes)))
cvx_end
