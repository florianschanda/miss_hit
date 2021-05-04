cvx_begin gp
    % optimization variables
    variables w(N) h(N) v(N+1) y(N+1)
    
    % objective is the total volume of the beam
    % obj = sum of (widths*heights*lengths) over each section
    % (recall that the length of each segment is set to be 1)
    minimize(w' * h)
    subject to
        % non-recursive formulation
        d = 6 * F * ones(N, 1) ./ (E * ones(N, 1) .* w .* h.^3);
        for i = 1:N
            (2 * i - 1) * d(i) + v(i + 1) <= v(i);
            (i - 1 / 3) * d(i) + v(i + 1) + y(i + 1) <= y(i);
        end
        
        % constraint set
        wmin <= w    <= wmax;
        hmin <= h    <= hmax;
        Smin <= h ./ w <= Smax;
        6 * F * [1:N]' ./ (w .* (h.^2)) <= sigma_max;
        y(1) <= ymax;
cvx_end
