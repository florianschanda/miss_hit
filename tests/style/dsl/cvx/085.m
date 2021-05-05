cvx_begin
    variables yhat(m) g(m)
    minimize(norm(yns - yhat))
    subject to
        yhat * ones(1, m) >= ones(m, 1) * yhat' + (ones(m, 1) * g') .* (u * ones(1, m) - ones(m, 1) * u');
cvx_end
