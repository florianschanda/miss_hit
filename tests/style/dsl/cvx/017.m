cvx_begin gp
    % optimization variables
    variable x(N)                 % sizes
    variable T(N)                 % arrival times
    
    % minimize the sum of scale factors subject to above constraints
    minimize(sum(x))
    subject to
        
        % input capacitance is an affine function of sizes
        Cin  = Cin_norm .* x;
        Cint = Cint_norm .* x;
        
        % driving resistance is inversily proportional to sizes
        R = Rdrv_norm ./ x;
        
        % gate delay is the product of its driving resistance and load cap.
        Cload = cvx(zeros(N, 1));
        for gate = 1:N
            if ~ismember(FO{gate}, primary_outputs)
                Cload(gate) = sum(Cin(FO{gate}));
            else
                Cload(gate) = Cin_po(FO{gate});
            end
        end
        
        % delay
        D = 0.69 * ones(N, 1) .* R .* (Cint + Cload);
        
        % create timing constraints
        for gate = 1:N
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
        
        % circuit delay is the max of arrival times for output gates
        output_gates = [FI{primary_outputs}];
        circuit_delay = max(T(output_gates));
        
        % collect all the constraints
        circuit_delay <= Dmax;
        x_min <= x <= x_max;
cvx_end
