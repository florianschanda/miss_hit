cvx_begin gp quiet
    variables h w d
    % objective function is the box volume
    maximize(h * w * d)
    subject to
        2 * (h * w + h * d) <= Awall_k;
        w * d <= Afloor_n;
        alpha <= h / w <= beta;
        gamma <= d / w <= delta;
cvx_end
