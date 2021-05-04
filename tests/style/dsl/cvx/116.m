cvx_begin
    variable w(n*P) complex
    minimize(max(abs(As * w)))
    subject to
        % target direction equality constraint
        Atar * w == 1;
cvx_end
