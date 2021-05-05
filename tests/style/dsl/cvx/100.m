cvx_begin
    variable r(n,1)
    
    % this is a feasibility problem
    minimize(max(abs(As * r)))
    subject to
        % passband constraints
        Ap * r >= (Lp.^2);
        Ap * r <= (Up.^2);
        % nonnegative-real constraint for all frequencies (a bit redundant)
        A * r >= 0;
cvx_end
