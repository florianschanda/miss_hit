cvx_begin
    variable x_opt(n)
    maximize sum(Pi.*log(P*x_opt))
    sum(x_opt) == 1;
    x_opt >= 0;
cvx_end
