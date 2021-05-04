cvx_begin
    variable x(2)
    minimize (sum(square_pos(norms(x * ones(1, K) - P, 2))))
cvx_end
