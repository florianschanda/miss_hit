cvx_begin
    variable x(n)
    dual variables lam1 lam2 lam3
    minimize(0.5 * quad_form(x, P0) + q0' * x + r0)
    lam1:0.5 * quad_form(x, P1) + q1' * x + r1 <= 0;
    lam2:0.5 * quad_form(x, P2) + q2' * x + r2 <= 0;
    lam3:0.5 * quad_form(x, P3) + q3' * x + r3 <= 0;
cvx_end
