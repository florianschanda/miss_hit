cvx_begin sdp quiet
    variable P(n,n) symmetric
    variables q(n) r tau(m)
    dual variables Z{m}
    maximize(1 - trace(Sigma * P) - r)
    subject to
        for i = 1:m
            qadj = q - 0.5 * tau(i) * A(i, :)';
            radj = r - 1 + tau(i) * b(i);
            [P, qadj; qadj', radj] >= 0:Z{i};
        end
        [P, q; q', r] >= 0;
        tau >= 0;
cvx_end
