cvx_begin
    variable x(n)
    minimize -sum(w.*log(b-A*x))
cvx_end
