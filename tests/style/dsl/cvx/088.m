cvx_begin gp
    variable d(n)
    minimize(sqrt(sum(sum(diag(d.^2) * (M.^2) * diag(d.^-2)))))
    % Alternate formulation: norm( diag(d)*abs(M)*diag(1./d), 'fro' )
cvx_end
