cvx_begin sdp quiet
    variables t lambda xrob(n)
    minimize(t + lambda)
    subject to
        [eye(m) A1 * xrob A2 * xrob A0 * xrob - b; ...
        [A1 * xrob A2 * xrob]' lambda * eye(2) zeros(2, 1); ...
        [A0 * xrob - b]' zeros(1, 2) t] >= 0;
cvx_end
