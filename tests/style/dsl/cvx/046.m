cvx_begin sdp quiet
    variable X(n,n) symmetric
    minimize (norm(X - X0, 'fro'))
    X >= 0;
cvx_end
