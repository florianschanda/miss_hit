cvx_begin
    variables a(np) t(1)
    minimize (t)
    a' * monX <= t;
    a' * monY >= -t;
    % For normalization purposes only
    norm(a) <= 1;
cvx_end
