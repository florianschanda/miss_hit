cvx_begin
    variables x(n) y(n)
    minimize (norm(x - y))
    A1 * x <= b1;
    A2 * y <= b2;
cvx_end
