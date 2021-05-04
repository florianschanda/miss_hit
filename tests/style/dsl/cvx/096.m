cvx_begin
    variable x1(n)
    minimize(matrix_frac(A * x1 + b, eye(m) + B * diag(x1) * B'))
    x1 >= 0;
cvx_end
cvx_begin
    variable x2(n)
    variable Y(n,n) diagonal
    minimize(matrix_frac(A * x2 + b, eye(m) + B * Y * B'))
    x2 >= 0;
    Y == diag(x2);
cvx_end
cvx_begin
    variables x3(n) w(n) v(m)
    minimize(square_pos(norm(v)) + matrix_frac(w, diag(x3)))
    v + B * w == A * x3 + b;
    x3 >= 0;
cvx_end
cvx_begin
    variables x4(n) w(n) v(m)
    variable Y(n,n) diagonal
    minimize(square_pos(norm(v)) + matrix_frac(w, Y))
    v + B * w == A * x4 + b;
    x4 >= 0;
    Y == diag(x4);
cvx_end
