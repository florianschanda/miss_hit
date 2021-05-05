cvx_begin
    variables x(n) y(n) w(n)
    dual variables lam muu z
    minimize (norm(w, 2))
    subject to
        lam:square_pos(norm (A * x + b)) <= 1;
        muu:square_pos(norm (C * y + d)) <= 1;
        z:x - y == w;
cvx_end
