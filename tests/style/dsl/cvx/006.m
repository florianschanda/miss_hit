cvx_begin
    variable x(n)
    dual variable y
    minimize(norm(A * x - b, p))
    subject to
        y:C * x == d;
cvx_end
