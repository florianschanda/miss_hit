cvx_begin sdp
    variable P(n,n) symmetric
    variables q(n) r(1)
    P <= -eye(n);
    sum((X' * P) .* X', 2) + X' * q + r >= +1;
    sum((Y' * P) .* Y', 2) + Y' * q + r <= -1;
cvx_end
