cvx_begin quiet
    variable x(1)
    minimize (quad_form(x, 1) + 1)
    quad_form(x, 1) - 6 * x + 8 <= u(i);
cvx_end
