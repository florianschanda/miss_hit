cvx_begin gp
    % optimization variables
    variables z(n) t(q) s(m)
    
    minimize(prod(t) * prod(s))
    subject to
        for k = 1:q
            prod(z.^(X(k, :)')) <= t(k);
        end
        
        for k = 1:m
            1 + prod(z.^(-X(k, :)')) <= s(k);
        end
cvx_end
