cvx_begin
    variable x(n)
    minimize -sum(log(b-A*x))
    F * x == g;
cvx_end
