cvx_begin quiet
    variables r_cur(n_cur,1)
    minimize(max(abs(As * r_cur)))
    10^(-delta / 10) <= Ap * r_cur <= 10^(+delta / 10);
    A * r_cur >= 0;
cvx_end
