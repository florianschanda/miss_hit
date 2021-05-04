cvx_begin
    variable w(n) complex
    minimize(max(abs(As * w)))
    subject to
        Atar * w == 1;   % target constraint
        if HAS_NULLS   % nulls constraints
            Anull * w == 0;
        end
cvx_end
