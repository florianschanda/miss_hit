cvx_begin
    variable x(n)
    maximize sum(entr(x))
    A * x == b;
    F * x <= g;
cvx_end
