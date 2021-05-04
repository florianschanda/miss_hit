cvx_begin
    variable x(30561)
    minimize(sum_square(A * x - b) + norm(x, 1))
cvx_end
