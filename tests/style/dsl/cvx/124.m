cvx_begin gp quiet
    variables wa wb wc wd ha hb hc hd
    % objective function is the area of the bounding box
    minimize(max(wa + wb, wc + wd) * (max(ha, hb) + max(hc, hd)))
    subject to
        % constraints (now impose the non-changing constraints)
        ha * wa == a;
        hb * wb == b;
        hc * wc == c;
        hd * wd == d;
        1 / alpha(n) <= ha / wa <= alpha(n);
        1 / alpha(n) <= hb / wb <= alpha(n);
        1 / alpha(n) <= hc / wc <= alpha(n);
        1 / alpha(n) <= hd / wd <= alpha(n);
cvx_end
