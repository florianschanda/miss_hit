cvx_begin gp quiet
    % optimization variables
    variables v(M) y(M) w(M)
    
    % objective function is the base transmit time
    tau_B = C * w(1);
    
    minimize(tau_B)
    subject to
        % fixed problem constraints
        Nmin <= v <= Nmax;
        
        for i = 1:M - 1
            y(i + 1) + v(i)^pwj <= y(i);
            w(i + 1) + y(i) * v(i)^pwi <= w(i);
        end
        
        % equalities
        y(M) == v(M)^pwj;
        w(M) == y(M) * v(M)^pwi;
        
        % changing constraint
        (WB * beta_min_GE(k) / (M * Nref^(g1 - g2) * Dn0)) * y(1) <= 1;
cvx_end
