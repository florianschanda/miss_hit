cvx_begin gp
    variables v(M) y(M) w(M)
    
    % objective function is the base transmit time
    tau_B = C * w(1);
    
    minimize(tau_B)
    subject to
        % problem constraints
        v >= Nmin;
        v <= Nmax;
        
        for i = 1:M - 1
            if mod(i, 100) == 0 fprintf(1, 'progress counter: %d\n', i);
            end
            y(i + 1) + v(i)^pwj <= y(i);
            w(i + 1) + y(i) * v(i)^pwi <= w(i);
        end
        
        y(M) == v(M)^pwj;
        w(M) == y(M) * v(M)^pwi;
cvx_end
