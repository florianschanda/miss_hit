cvx_begin gp
    variable P(n)
    % objective function is the total transmitter power
    minimize(sum(P))
    subject to
        % formulate the inverse SINR at each receiver using vectorize features
        Gdiag = diag(G);          % the main diagonal of G matrix
        Gtilde = G - diag(Gdiag); % G matrix without the main diagonal
        % inverse SINR
        inverseSINR = (sigma + Gtilde * P) ./ (Gdiag .* P);
        % constraints are power limits and minimum SINR level
        Pmin <= P <= Pmax;
        inverseSINR <= (1 / SINR_min);
cvx_end
