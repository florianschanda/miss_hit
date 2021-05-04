cvx_begin
    variable hf(n,1)
    minimize(max(abs(G .* (A * hf) - Gdes)))
cvx_end
cvx_begin
    variable t
    variable ht(n,1)
    
    minimize(max(abs(Tconv(times_not_D, :) * ht)))
    subject to
        Tconv(D + 1, :) * ht == 1;
cvx_end
