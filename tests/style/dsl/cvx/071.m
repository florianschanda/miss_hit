cvx_begin quiet
    variable xhub(n)
    minimize(sum(huber(A * xhub - b)))
cvx_end
