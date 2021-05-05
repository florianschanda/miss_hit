cvx_begin
    variable x(n)
    maximize(sum(log(x)))
    subject to
        A * x <= c;
cvx_end
cvx_begin
    variable lambda(L)
    minimize(c' * lambda - sum(log(A' * lambda)) - n)
    subject to
        lambda >= 0;
cvx_end
