cvx_begin
    variable x(n)
    dual variables y z
    minimize(c' * x + d)
    subject to
        y:A * x == b;
        z:x >= 0;
cvx_end
