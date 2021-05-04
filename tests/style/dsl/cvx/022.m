cvx_begin
    variables lambda(m)
    minimize(sum(lambda))
    subject to
        A' * lambda == 0;
        b' * lambda == -1;
        lambda >= 0;
cvx_end
