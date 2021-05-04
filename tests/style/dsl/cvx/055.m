cvx_begin
    variables a(n) b(1) t(1)
    maximize (t)
    X' * a - b >= t;
    Y' * a - b <= -t;
    norm(a) <= 1;
cvx_end
