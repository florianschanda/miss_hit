cvx_begin
    variable w(n) complex
    minimize(norm(w))
    subject to
        Atar * w == 1;
        abs(As * w) <= 10^(min_sidelobe / 20);
cvx_end
