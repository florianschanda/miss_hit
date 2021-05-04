cvx_begin
    variables x1(n) x2(n) x3(n)
    minimize (norm([A1 * x1 A2 * x2 A3 * x3] - v'))
    % continuity conditions at point a
    [1 a a^2   a^3] * x1 == [1 a a^2   a^3] * x2;
    [0 1 2 * a 3 * a^2] * x1 == [0 1 2 * a 3 * a^2] * x2;
    [0 0   2 6 * a] * x1 == [0 0   2 6 * a] * x2;
    % continuity conditions at point b
    [1 b b^2   b^3] * x2 == [1 b b^2   b^3] * x3;
    [0 1 2 * b 3 * b^2] * x2 == [0 1 2 * b 3 * b^2] * x3;
    [0 0   2 6 * b] * x2 == [0 0   2 6 * b] * x3;
cvx_end
cvx_begin
    variables xl1(n) xl2(n) xl3(n)
    minimize (norm([A1 * xl1 A2 * xl2 A3 * xl3] - v', inf))
    % continuity conditions at point a
    [1 a a^2   a^3] * xl1 == [1 a a^2   a^3] * xl2;
    [0 1 2 * a 3 * a^2] * xl1 == [0 1 2 * a 3 * a^2] * xl2;
    [0 0   2 6 * a] * xl1 == [0 0   2 6 * a] * xl2;
    % continuity conditions at point b
    [1 b b^2   b^3] * xl2 == [1 b b^2   b^3] * xl3;
    [0 1 2 * b 3 * b^2] * xl2 == [0 1 2 * b 3 * b^2] * xl3;
    [0 0   2 6 * b] * xl2 == [0 0   2 6 * b] * xl3;
cvx_end
