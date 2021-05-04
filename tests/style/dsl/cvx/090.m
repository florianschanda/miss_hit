cvx_begin
    variable r(1)
    variable x_c(2)
    maximize (r)
    a1' * x_c + r * norm(a1, 2) <= b(1);
    a2' * x_c + r * norm(a2, 2) <= b(2);
    a3' * x_c + r * norm(a3, 2) <= b(3);
    a4' * x_c + r * norm(a4, 2) <= b(4);
cvx_end
