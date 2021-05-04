cvx_begin sdp quiet
    variable x(m)
    variable G(n,n) symmetric
    variable C(n,n) symmetric
    minimize(L' * x)
    G == reshape(GG * [1; x], n, n);
    C == reshape(CC * [1; x], n, n);
    for k = 1:n
        delay * G - C + sparse(k, k, delay, n, n) >= 0;
    end
    0 <= x <= wmax;
cvx_end
