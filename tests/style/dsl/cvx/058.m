cvx_begin
    variables a(np) t(1)
    minimize (t)
    a' * monX <= t;
    a' * monY >= -t;
cvx_end
