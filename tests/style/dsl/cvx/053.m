cvx_begin
    variable x(N+M,2)
    minimize (sum(square_pos(norms(A * x, 2, 2))))
    x(N + [1:M], :) == fixed;
cvx_end
