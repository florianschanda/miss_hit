cvx_begin sdp quiet
    variable x(m)
    variable G(n,n) symmetric
    variable C(n,n) symmetric
    minimize(sum(x))
    G == reshape(GG * [1; x], n, n);
    C == reshape(CC * [1; x], n, n);
    delay * G - C >= 0;
    0 <= x <= wmax;
cvx_end
