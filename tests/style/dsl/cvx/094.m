cvx_begin sdp
    % A is a PSD symmetric matrix (n-by-n)
    variable A(n,n) symmetric
    A >= 0;
    
    % constrained matrix entries.
    A(1, 1) == 3;
    A(2, 2) == 2;
    A(3, 3) == 1;
    A(4, 4) == 5;
    % Note that because A is symmetric, these off-diagonal
    % constraints affect the corresponding element on the
    % opposite side of the diagonal.
    A(1, 2) == .5;
    A(1, 4) == .25;
    A(2, 3) == .75;
    
    % find the solution to the problem
    maximize(log_det(A))
    % maximize( det_rootn( A ) )
cvx_end
