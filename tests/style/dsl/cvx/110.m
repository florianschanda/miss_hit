cvx_begin quiet
    variable h_cur(n_cur+1,1)
    minimize(max(abs(As * h_cur)))
    10^(-delta / 20) <= Ap * h_cur <=  10^(+delta / 20);
cvx_end
