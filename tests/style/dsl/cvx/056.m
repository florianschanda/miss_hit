cvx_begin sdp
    variable C1(n,n) symmetric
    maximize (C1(1, 4))
    C1 >= 0;
    diag(C1) == ones(n, 1);
    C1(1, 2) >= 0.6;
    C1(1, 2) <= 0.9;
    C1(1, 3) >= 0.8;
    C1(1, 3) <= 0.9;
    C1(2, 4) >= 0.5;
    C1(2, 4) <= 0.7;
    C1(3, 4) >= -0.8;
    C1(3, 4) <= -0.4;
cvx_end
cvx_begin sdp
    variable C2(n,n) symmetric
    minimize (C2(1, 4))
    C2 >= 0;
    diag(C2) == ones(n, 1);
    C2(1, 2) >= 0.6;
    C2(1, 2) <= 0.9;
    C2(1, 3) >= 0.8;
    C2(1, 3) <= 0.9;
    C2(2, 4) >= 0.5;
    C2(2, 4) <= 0.7;
    C2(3, 4) >= -0.8;
    C2(3, 4) <= -0.4;
cvx_end
