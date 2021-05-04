cvx_begin sdp
    variable Asqr(n,n) symmetric
    variable btilde(n)
    variable t(m)
    maximize(det_rootn(Asqr))
    subject to
        t >= 0;
        for i = 1:m
            [-(Asqr - t(i) * As{i}), -(btilde - t(i) * bs{i}), zeros(n, n)
            -(btilde - t(i) * bs{i})', -(-1 - t(i) * cs{i}), -btilde'
            zeros(n, n), -btilde, Asqr] >= 0;
        end
cvx_end
