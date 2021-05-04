cvx_begin gp quiet
    % optimization variables
    variable x(m)           % scale factors
    
    % input capacitance is an affine function of sizes
    cin = alpha + beta .* x;
    
    % load capacitance of a gate is the sum of its fan-out c_in's
    clear cload; % start with a fresh variable
    cload(1) = cin(4);
    cload(2) = cin(4) + cin(5);
    cload(3) = cin(5) + cin(7);
    cload(4) = cin(6) + cin(7);
    cload(5) = cin(7);
    % output gates have their load capacitances
    cload(6) = Cout6;
    cload(7) = Cout7;
    
    % gate delay is the product of its driving res. R = gamma./x and cload
    d = (cload') .* gamma ./ x;
    
    power = (f .* e)' * x;         % total power
    area = a' * x;               % total area
    
    % evaluate delay over all paths in the given circuit (there are 7 paths)
    path_delays = [ ...
    d(1) + d(4) + d(6)  % delay of path 1
    d(1) + d(4) + d(7)  % delay of path 2, etc...
    d(2) + d(4) + d(6)
    d(2) + d(4) + d(7)
    d(2) + d(5) + d(7)
    d(3) + d(5) + d(6)
    d(3) + d(7)];
    
    % overall circuit delay
    circuit_delay = (max(path_delays));
    
    % objective is the worst-case delay
    minimize(circuit_delay)
    subject to
        % construct the constraints
        x >= 1;             % all sizes greater than 1 (normalized)
        power <= Pmax(n);   % power constraint
        area <= Amax(k);    % area constraint
cvx_end
