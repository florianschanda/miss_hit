cvx_begin quiet
    variables x(n) y(n) w(n) h(n) W H
    minimize (W + H)
    x >= r;
    y >= r;
    w >= 0;
    h >= 0;
    x(5) + w(5) + r <= W;    % No rectangles at the right of Rectangle 5
    x(1) + w(1) + r <= x(3); % Rectangle 1 is at the left of Rectangle 3
    x(2) + w(2) + r <= x(3); % Rectangle 2 is at the left of Rectangle 3
    x(3) + w(3) + r <= x(5); % Rectangle 3 is at the left of Rectangle 5
    x(4) + w(4) + r <= x(5); % Rectangle 4 is at the left of Rectangle 5
    y(4) + h(4) + r <= H;    % No rectangles on top of Rectangle 4
    y(5) + h(5) + r <= H;    % No rectangles on top of Rectangle 5
    y(2) + h(2) + r <= y(1); % Rectangle 2 is below Rectangle 1
    y(1) + h(1) + r <= y(4); % Rectangle 1 is below Rectangle 4
    y(3) + h(3) + r <= y(4); % Rectangle 3 is below Rectangle 4
    w <= 5 * h;                % Aspect ratio constraints
    h <= 5 * w;
    w' >= quad_over_lin([A.^.5; zeros(1, n)], h');
cvx_end
