cvx_begin
    variable x1(n)
    minimize(sum(huber(A * x1 - b, M)))
cvx_end
cvx_begin
    variable x2(n)
    variable w(m)
    minimize(sum(quad_over_lin(diag(A * x2 - b), w' + 1)) + M^2 * ones(1, m) * w)
    w >= 0;
cvx_end
cvx_begin
    variable x3(n)
    variable u(m)
    variable v(m)
    minimize(sum(square(u) +  2 * M * v))
    A * x3 - b <= u + v;
    A * x3 - b >= -u - v;
    u >= 0;
    u <= M;
    v >= 0;
cvx_end
