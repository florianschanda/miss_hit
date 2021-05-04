cvx_begin
    variables lam(m) muu(m) z(n)
    maximize (-b1' * lam - b2' * muu)
    A1' * lam + z == 0;
    A2' * muu - z == 0;
    norm(z) <= 1;
    -lam <= 0;
    -muu <= 0;
cvx_end
