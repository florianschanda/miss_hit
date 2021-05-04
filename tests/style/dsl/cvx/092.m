cvx_begin sdp
    variable t
    minimize (c * t)
    A >= t * B;
cvx_end
