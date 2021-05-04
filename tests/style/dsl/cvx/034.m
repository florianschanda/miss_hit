cvx_begin
    variables a(n) b(1) u(N) v(M)
    minimize (ones(1, N) * u + ones(1, M) * v)
    X' * a - b >= 1 - u;
    Y' * a - b <= -(1 - v);
    u >= 0;
    v >= 0;
cvx_end
