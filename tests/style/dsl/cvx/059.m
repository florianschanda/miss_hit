cvx_begin
    variables x(n) y(n)
    minimize (norm(x - y))
    norm(x, 1) <= 2;
    norm(y - [4; 3], inf) <= 1;
cvx_end
