cvx_begin
    variable delta
    variable h(n+1,1)
    
    minimize(delta)
    subject to
        % passband bounds
        Ap * h <= delta;
        inv_pos(Ap * h) <= delta;
        
        % stopband bounds
        abs(As * h) <= Us;
cvx_end
