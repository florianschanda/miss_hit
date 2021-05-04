cvx_begin quiet
    variable w(n) complex
    % feasibility problem
    Atar * w == 1;
    abs(As * w) <= 10^(min_sidelobe / 20);
cvx_end
cvx_begin quiet
    variable w(n) complex
    minimize(norm(w))
    subject to
        Atar * w == 1;
        abs(As * w) <= 10^(min_sidelobe / 20);
cvx_end
