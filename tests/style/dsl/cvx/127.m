cvx_begin gp quiet
    % optimization variables
    variable x(m)                 % scale factors
    variable t(m)                 % arrival times
    
    % objective is the upper bound on the overall delay
    % and that is the max of arrival times for output gates 6 and 7
    minimize(max(t(6), t(7)))
    subject to
        % input capacitance is an affine function of sizes
        cin = alpha + beta .* x;
        
        % load capacitance is the input capacitance times the fan-out matrix
        % given by Fout = Aout*Ain'
        cload = (Aout * Ain') * cin;
        cload(6) = Cout6;          % load capacitance of the output gate 6
        cload(7) = Cout7;          % load capacitance of othe utput gate 7
        
        % delay is the product of its driving resistance R = gamma./x and cload
        d = cload .* gamma ./ x;
        
        % power and area definitions
        power = (f .* e)' * x;
        area = a' * x;
        
        % scale size, power, and area constraints
        x >= 1;
        power <= Pmax(n);
        area <= Amax(k);
        
        % create timing constraints
        % these constraints enforce t_j + d_j <= t_i over all gates j that drive gate i
        Aout' * t + Ain' * d <= Ain' * t;
        
        % for gates with inputs not connected to other gates we enforce d_i <= t_i
        d(1:3) <= t(1:3);
cvx_end
