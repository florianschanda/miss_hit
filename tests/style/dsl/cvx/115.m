cvx_begin sdp
    variable S(n,n) symmetric
    maximize log_det(S) - trace(S*Y)
    sum(sum(abs(S))) <= alpha;
    S >= 0;
cvx_end
