cvx_begin quiet
    if mod(iter, 2) == 1
        variable X(k,n)
        X >= 0;
    else
        variable Y(m,k)
        Y >= 0;
    end
    minimize(norm(A - Y * X, 'fro'))
cvx_end
