cvx_begin
    variables x(2)
    maximize(y' * U * x - sum(log_sum_exp([zeros(1, m) x' * U'])))
cvx_end
