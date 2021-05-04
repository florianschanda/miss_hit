cvx_begin
    variable x(N+M,2)
    minimize (sum(norms(A * x, 2, 2)))
    x(N + [1:M], :) == fixed;
cvx_end
