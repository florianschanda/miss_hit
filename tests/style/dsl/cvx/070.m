cvx_begin
    variables a(n) b(1)
    maximize sum(y.*log(a'*u+b) - (a'*u+b))
cvx_end
