cvx_begin quiet
    variable x(n)
    minimize (norm(x - corrupt) + lambdas(i) * norm(D * x))
cvx_end
