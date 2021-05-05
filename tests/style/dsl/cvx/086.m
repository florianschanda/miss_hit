cvx_begin
    variable x(n)
    minimize ((1 / 2) * quad_form(x, P) + q' * x + r)
    x >= -1;
    x <=  1;
cvx_end
