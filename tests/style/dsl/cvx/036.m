cvx_begin
    variable B(n,n) symmetric
    variable d(n)
    maximize(det_rootn(B))
    subject to
        for i = 1:m
            norm(B * A(i, :)', 2) + A(i, :) * d <= b(i);
        end
cvx_end
