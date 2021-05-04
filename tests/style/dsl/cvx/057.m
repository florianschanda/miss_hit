cvx_begin quiet
    variables x(n) y(n) w(n) h(n) W H
    minimize (W + H)
    w >= 0;
    h >= 0;
    x(leafs_H) >= rho;
    y(leafs_V) >= rho;
    x(roots_H) + w(roots_H) + rho <= W;
    y(roots_V) + h(roots_V) + rho <= H;
    for i = 1:length(nodes_H)
        node = nodes_H(i);
        c = adj_H(node, :);
        prnt = find(c > 0)';
        m = length(prnt);
        x(node) + w(node) + rho <= x(prnt);
    end
    
    for i = 1:length(nodes_V)
        node = nodes_V(i);
        c = adj_V(node, :);
        prnt = find(c > 0)';
        m = length(prnt);
        y(node) + h(node) + rho <= y(prnt);
    end
    
    if sum(size(u)) ~= 0
        h <= u .* w;
    end
    if sum(size(l)) ~= 0
        h >= l .* w;
    end
    w' >= quad_over_lin([Amin.^.5; zeros(1, n)], h');
cvx_end
