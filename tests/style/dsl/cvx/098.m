cvx_begin gp
    % optimization variables
    variables lambda b(4) s(3) v(4) c(2)
    
    % objective is the Perron-Frobenius eigenvalue
    minimize(lambda)
    subject to
        % inequality constraints
        b' * v      <= lambda * v(1);
        s(1) * v(1) <= lambda * v(2);
        s(2) * v(2) <= lambda * v(3);
        s(3) * v(3) <= lambda * v(4);
        [0.5; 0.5] <= c;
        c <= [2; 2];
        % equality constraints
        b == b_nom .* ((ones(4, 1) * (c(1) / c_nom(1))).^alpha) .* ...
        ((ones(4, 1) * (c(2) / c_nom(2))).^beta);
        s == s_nom .* ((ones(3, 1) * (c(1) / c_nom(1))).^gamma) .* ...
        ((ones(3, 1) * (c(2) / c_nom(2))).^delta);
cvx_end
