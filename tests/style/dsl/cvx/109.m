cvx_begin
    variable r(n,1)   % auto-correlation coefficients
    variable R(m,1)   % power spectrum
    
    % log-chebychev minimax design
    minimize(max(max([R ./ (D.^2)  (D.^2) .* inv_pos(R)]')))
    subject to
        % power spectrum constraint
        R == Al * r;
cvx_end
