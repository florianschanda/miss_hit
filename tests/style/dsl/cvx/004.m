cvx_begin
    variable x(n)
    dual variables y z
    minimize(c' * x + d)
    subject to
        y:A * x <= b;
cvx_end
