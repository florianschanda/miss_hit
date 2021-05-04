cvx_begin
    variable h(n+1,1)
    minimize(norm(As * h, Inf))
    subject to
        10^(-ripple / 20) <= Ap * h <= 10^(ripple / 20);
cvx_end
