cvx_begin gp
    % optimization variables
    variables w(N) h(N)
    
    % setting up variables relations
    % (recursive formulation)
    v = cvx(zeros(N + 1, 1));
    y = cvx(zeros(N + 1, 1));
    for i = N:-1:1
        fprintf(1, 'Building recursive relations for index: %d\n', i);
        v(i) = 12 * (i - 1 / 2) * F / (E * w(i) * h(i)^3) + v(i + 1);
        y(i) = 6 * (i - 1 / 3) * F / (E * w(i) * h(i)^3)  + v(i + 1) + y(i + 1);
    end
    
    % objective is the total volume of the beam
    % obj = sum of (widths*heights*lengths) over each section
    % (recall that the length of each segment is set to be 1)
    minimize(w' * h)
    subject to
        % constraint set
        wmin <= w    <= wmax;
        hmin <= h    <= hmax;
        Smin <= h ./ w <= Smax;
        6 * F * [1:N]' ./ (w .* (h.^2)) <= sigma_max;
        y(1) <= ymax;
cvx_end
