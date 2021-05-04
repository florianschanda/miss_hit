cvx_begin gp quiet
    % optimization variables
    variable w(N-1)     % wire width
    variable T(N)       % arrival time (Elmore delay to node i)
    
    % area definition
    area = sum(w .* l);
    
    % wire segment resistance is inversely proportional to widths
    R = alpha .* l ./ w;
    R = [Rsource; R];
    
    % wire segment capacitance is an affine function of widths
    C_bar = beta .* l .* w + gamma .* l;
    C_bar = [0; C_bar];
    
    % compute common capacitances for each node (C_tilde in GP tutorial)
    C_tilde = cvx(zeros(N, 1));
    for node = [1:N]
        C_tilde(node, 1) = Cload(node);
        for k = parent(node)
            if k > 0
                C_tilde(node, 1) = C_tilde(node, 1) + C_bar(k);
            end
        end
        for k = children{node}
            C_tilde(node, 1) = C_tilde(node, 1) + C_bar(k);
        end
    end
    
    % now compute total downstream capacitances
    C_total = C_tilde;
    for node = N:-1:1
        for k = children{node}
            C_total(node, 1) = C_total(node, 1) + C_total(k, 1);
        end
    end
    
    % objective is the critical Elmore delay
    minimize(max(T(leafs)))
    subject to
        % generate Elmore delay constraints
        R(1) * C_total(1) <= T(1, 1);
        for node = 2:N
            R(node) * C_total(node) + T(parent(node), 1) <= T(node, 1);
        end
        
        % area and width constraints
        area <= Amax;
        w >= Wmin;
        w <= Wmax;
cvx_end
