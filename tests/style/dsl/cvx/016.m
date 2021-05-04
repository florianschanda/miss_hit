cvx_begin gp quiet
    % optimization variables
    variable x(m)                 % scale factor
    variable T(m)                 % arrival times
    
    % input capacitance is an affine function of sizes
    Cin  = Cin_norm .* x;
    Cint = Cint_norm .* x;
    
    % driving resistance is inversily proportional to sizes
    R = Rdrv_norm ./ x;
    
    % gate delay is the product of its driving resistance and load cap.
    Cload = cvx(zeros(m, 1));
    for gate = 1:m
        if ~ismember(FO{gate}, primary_outputs)
            Cload(gate) = sum(Cin(FO{gate}));
        else
            Cload(gate) = Cin_po(FO{gate});
        end
    end
    
    % delay
    D = 0.69 * ones(m, 1) .* R .* (Cint + Cload);
    
    % total area
    area = A_norm' * x;
    
    % total power calculation
    Pdyn = Vdd^2 * sum(f_pi(primary_inputs) .* Cload_pi(primary_inputs)) + ...
    Vdd^2 * (f_gates' * (Cint + Cload));
    Pstat = Vdd * Ileak_norm' * x;
    power = Pdyn + Pstat;
    
    minimize(max(T(output_gates)))
    subject to
        % constraints
        x >= 1;
        area <= Amax;
        power <= Pmax(n);
        
        % create timing constraints
        for gate = 1:m
            if ~ismember(FI{gate}, primary_inputs)
                for j = FI{gate}
                    % enforce T_j + D_j <= T_i over all gates j that drive i
                    D(gate) + T(j) <= T(gate);
                end
            else
                % enforce D_i <= T_i for gates i connected to primary inputs
                D(gate) <= T(gate);
            end
        end
cvx_end
