cvx_begin
    variables T( m, n ) D( m, m )
    minimize max( D(1,2), D(2,1) )
    subject to
        D == T * P;
        sum(T, 1) == 1;
        T >= 0;
cvx_end
