cvx_begin sdp
    variable X( n, n ) symmetric
    dual variable y{n}
    dual variable Z
    minimize((n - 1:-1:0) * diag(X))
    for k = 1:n
        sum(diag(X, k - 1)) == b(k):y{k};
    end
    X >= 0:Z;
cvx_end
