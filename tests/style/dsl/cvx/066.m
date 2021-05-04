cvx_begin
    variables pent(n)
    maximize(sum(entr(pent)))
    sum(pent) == 1;
    A * pent <= b;
cvx_end
cvx_begin quiet
    variable p( n )
    minimize sum( p(1:t) )
    p >= 0;
    sum(p) == 1;
    A * p <= b;
cvx_end
cvx_begin quiet
    variable p( n )
    maximize sum( p(1:t) )
    p >= 0;
    sum(p) == 1;
    A * p <= b;
cvx_end
