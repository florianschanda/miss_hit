cvx_begin
    variables a(n) b(1)
    X' * a - b >= 1;
    Y' * a - b <= -1;
cvx_end
