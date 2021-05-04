cvx_begin
    variable x1(n)
    minimize(norm(A * x1 + b, 1))
cvx_end
cvx_begin
    variable xdz(n)
    minimize(sum(max(abs(A * xdz + b) - dz, 0)))
cvx_end
cvx_begin
    variable xlb(n)
    minimize norm(A*xlb+b,Inf)
cvx_end
