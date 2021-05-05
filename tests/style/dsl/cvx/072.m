cvx_begin quiet
    variables u(m+1) g_x(m+1) g_y(m+1)
    minimize(u(k) - u(m + 1))
    subject to
        g_x >= 0;
        g_y >= 0;
        ones(m + 1, 1) * u' <= u * ones(1, m + 1) + (g_x * ones(1, m + 1)) .* ...
        (ones(m + 1, 1) * data(:, 1)' - data(:, 1) * ones(1, m + 1)) + ...
        (g_y * ones(1, m + 1)) .* (ones(m + 1, 1) * data(:, 2)' - data(:, 2) * ones(1, m + 1));
        (u * ones(1, m + 1)) .* Pweak >= (ones(m + 1, 1) * u') .* Pweak;
cvx_end
cvx_begin quiet
    variables u(m+1) g_x(m+1) g_y(m+1)
    maximize(u(k) - u(m + 1))
    subject to
        g_x >= 0;
        g_y >= 0;
        ones(m + 1, 1) * u' <= u * ones(1, m + 1) + (g_x * ones(1, m + 1)) .* ...
        (ones(m + 1, 1) * data(:, 1)' - data(:, 1) * ones(1, m + 1)) + ...
        (g_y * ones(1, m + 1)) .* (ones(m + 1, 1) * data(:, 2)' - data(:, 2) * ones(1, m + 1));
        (u * ones(1, m + 1)) .* Pweak >= (ones(m + 1, 1) * u') .* Pweak;
cvx_end
