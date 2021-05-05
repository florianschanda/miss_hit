cvx_begin sdp quiet
    variables w(m,3) t(m,2) s(1,2)
    variable G(N,N) symmetric
    variable C(N,N) symmetric
    minimize(sum(s))
    subject to
        G == reshape(GG * [1; w(:)], N, N);
        C == reshape(CC * [1; w(:); t(:)], N, N);
        delay * G - C >= 0;
        wmin <= w(:) <= wmax;
        t(:) <= 1 / smin;
        s(:) <= smax;
        inv_pos(t(:, 1)) <= s(1) - w(:, 1) - 0.5 * w(:, 2);
        inv_pos(t(:, 2)) <= s(2) - w(:, 3) - 0.5 * w(:, 2);
cvx_end
