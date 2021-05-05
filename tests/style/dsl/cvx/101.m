cvx_begin quiet
    variable h_cur(n+1,1)
    % feasibility problem
    % passband bounds
    Ap * h_cur <= 10^(delta / 20);
    Ap * h_cur >= 10^(-delta / 20);
    % stopband bounds
    abs(As * h_cur) <= 10^(atten_level / 20);
cvx_end
