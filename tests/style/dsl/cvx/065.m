cvx_begin sdp
    variable S(n,n) symmetric
    maximize(log_det(S) - trace(S * Y))
    S >= Ui;
    S <= Li;
cvx_end
