cvx_begin quiet
    variable x(3)
    minimize (norm(A * x + b + epsilon(i) * d, 1))
cvx_end
