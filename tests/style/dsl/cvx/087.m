cvx_begin
    variable x(n)
    y = P * x;
    maximize (c' * x + sum(entr(y)) / log(2))
    x >= 0;
    sum(x) == 1;
cvx_end
