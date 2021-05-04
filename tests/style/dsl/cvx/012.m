cvx_begin gp quiet
    if need_sedumi
        cvx_solver sedumi
    end
    
    % device width variables
    variable w(N)
    
    % device specs
    device(1:2) = PMOS;
    device(3:4) = NMOS;
    
    for num = 1:N
        device(num).R   = device(num).R / w(num);
        device(num).Cdb = device(num).Cdb * w(num);
        device(num).Csb = device(num).Csb * w(num);
        device(num).Cgb = device(num).Cgb * w(num);
        device(num).Cgs = device(num).Cgs * w(num);
    end
    
    % capacitances
    C1 = sum([device(1:3).Cdb]) + Cload;
    C2 = device(3).Csb + device(4).Cdb;
    
    % input capacitances
    Cin_A = sum([device([2 3]).Cgb]) + sum([device([2 3]).Cgs]);
    Cin_B = sum([device([1 4]).Cgb]) + sum([device([1 4]).Cgs]);
    
    % resistances
    R = [device.R]';
    
    % area definition
    area = sum(w);
    
    % delays and dissipated energies for all six possible transitions
    % transition 1 is A: 1->1, B: 1->0, Z: 0->1
    D1 = R(1) * (C1 + C2);
    E1 = (C1 + C2) * Vdd^2 / 2;
    % transition 2 is A: 1->0, B: 1->1, Z: 0->1
    D2 = R(2) * C1;
    E2 = C1 * Vdd^2 / 2;
    % transition 3 is A: 1->0, B: 1->0, Z: 0->1
    % D3 = C1*R(1)*R(2)/(R(1) + R(2)); % not a posynomial
    E3 = C1 * Vdd^2 / 2;
    % transition 4 is A: 1->1, B: 0->1, Z: 1->0
    D4 = C1 * R(3) + R(4) * (C1 + C2);
    E4 = (C1 + C2) * Vdd^2 / 2;
    % transition 5 is A: 0->1, B: 1->1, Z: 1->0
    D5 = C1 * (R(3) + R(4));
    E5 = (C1 + C2) * Vdd^2 / 2;
    % transition 6 is A: 0->1, B: 0->1, Z: 1->0
    D6 = C1 * R(3) + R(4) * (C1 + C2);
    E6 = (C1 + C2) * Vdd^2 / 2;
    
    % objective is the worst-case delay
    minimize(max([D1 D2 D4]))
    subject to
        area <= Amax(k);
        w >= wmin;
cvx_end
