cvx_begin
    variable x_l1(n)
    minimize(norm(x_l1, 1))
    subject to
        A * x_l1 <= b;
cvx_end
cvx_begin quiet
    variable x_log(n)
    minimize(sum(W .* abs(x_log)))
    subject to
        A * x_log <= b;
cvx_end
