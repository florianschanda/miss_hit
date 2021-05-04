cvx_begin
    variable x(n)
    minimize(norm(A * x - b))
cvx_end
cvx_begin
    variable x(n)
    minimize(norm(A * x - b))
    subject to
        l <= x <= u;
cvx_end
cvx_begin
    variable x(n)
    minimize(norm(A * x - b, Inf))
cvx_end
cvx_begin
    variable x(n)
    minimize(norm(A * x - b, 1))
cvx_end
cvx_begin
    variable x(n)
    minimize(norm_largest(A * x - b, k))
cvx_end
cvx_begin
    variable x(n)
    minimize(sum(huber(A * x - b)))
cvx_end
cvx_begin
    variable x(n)
    minimize(norm(A * x - b))
    subject to
        C * x == d;
        norm(x, Inf) <= 1;
cvx_end
cvx_begin
    variable x(n)
    minimize(norm(A * x - b) + gamma(k) * norm(x, 1))
cvx_end
