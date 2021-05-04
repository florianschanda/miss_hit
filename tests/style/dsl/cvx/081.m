cvx_begin quiet
    variable x_nom(n)
    minimize (norm(A * x_nom - b))
cvx_end
cvx_begin quiet
    variable x_stoch(n)
    minimize (square_pos(norm(A * x_stoch - b)) + quad_form(x_stoch, P))
cvx_end
cvx_begin quiet
    variable x_wc(n)
    minimize (max(norm((A - B) * x_wc - b), norm((A + B) * x_wc - b)))
cvx_end
