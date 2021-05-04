cvx_begin
    variable lambda(p)
    maximize (det_rootn(V * diag(lambda) * V'))
    subject to
        sum(lambda) == 1;
        lambda >= 0;
cvx_end
cvx_begin sdp
    variables lambda(p) u(n)
    minimize (sum(u))
    subject to
        for k = 1:n
            [V * diag(lambda) * V'  e(:, k)
            e(k, :)             u(k)] >= 0;
        end
        sum(lambda) == 1;
        lambda >= 0;
cvx_end
cvx_begin sdp
    variables t lambda(p)
    maximize (t)
    subject to
        V * diag(lambda) * V' >= t * eye(n, n);
        sum(lambda) == 1;
        lambda >= 0;
cvx_end
