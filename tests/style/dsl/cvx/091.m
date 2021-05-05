cvx_begin
    variable r(1)
    variable x_c(n)
    dual variable y
    maximize (r)
    y:A * x_c + r * norm_ai <= b;
cvx_end
