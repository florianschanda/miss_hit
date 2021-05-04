cvx_begin sdp quiet
    variables w(m,2) d(1,2)
    variable G(n,n,2) symmetric
    variable C(n,n,2) symmetric
    minimize(L * sum(d) + sum(w(:)))
    G == reshape(GG * [1; w(:); d(:)], n, n, 2);
    C == reshape(CC * [1; w(:); d(:)], n, n, 2);
    % This is actually two LMIs, one for each circuit
    (delay / 2) * G - C >= 0;
    0 <= w(:) <= wmax;
    d(:) >= 0;
cvx_end
