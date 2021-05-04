cvx_begin quiet
    variable xrec(n+1)
    minimize(norm(xrec - corrupt))
    subject to
        norm(xrec(2:(n + 1)) - xrec(1:n), 1) <= TVs(i);
cvx_end
cvx_begin quiet
    variable xrec(n+1)
    minimize(norm(xrec - corrupt))
    subject to
        norm(xrec(2:(n + 1)) - xrec(1:n), 1) <= 10;
cvx_end
cvx_begin quiet
    variable xrec(n+1)
    minimize(norm(xrec - corrupt))
    subject to
        norm(xrec(2:(n + 1)) - xrec(1:n), 1) <= 8;
cvx_end
cvx_begin quiet
    variable xrec(n+1)
    minimize(norm(xrec - corrupt))
    subject to
        norm(xrec(2:(n + 1)) - xrec(1:n), 1) <= 5;
cvx_end
