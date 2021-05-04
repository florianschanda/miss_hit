cvx_begin sdp quiet
    variable S(n,n) symmetric
    maximize log_det(S) - trace(S*Y) - lambda(i)*sum(sum(abs(S)))
    S >= 0;
cvx_end
