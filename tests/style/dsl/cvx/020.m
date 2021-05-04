cvx_begin gp quiet
    % optimization variables
    variable D        % diameter of loop inductor
    variable W        % width of loop inductor
    variable SRF      % self resonance frequency
    variable l        % length of CMOS transistor
    variable w        % width of CMOS transistor
    variable Imax     % maximum current through CMOS transistor
    variable VOsc     % differential voltage amplitude
    variable CT       % total capacitance of oscillator
    variable Csw      % maximum switching capacitance
    variable Cvar     % minimum variable capacitance
    variable IBias    % bias current
    variable CMaxFreq % capacitor max frequency
    
    % minimize power = Vdd*IBias;
    minimize(Vdd * IBias)
    subject to
        % *******************************************%
        % loop inductor definitions and constraints %
        % *******************************************%
        SRFSpec  = 3 * F;
        omegaSRF = 2 * pi * SRF;
        
        % inductance
        L = 2.1e-06 * D^(1.28) * (W)^(-0.25) * (F)^(-0.01);
        % series resistance
        R = 0.1 * D / W + 3e-6 * D * W^(-0.84) * F^(0.5) + 5e-9 * D * W^(-0.76) * F^(0.75) + 0.02 * D * W * F;
        % effective capacitance
        C = 1e-11 * D + 5e-6 * D * W;
        
        % area, tank conductance, and inverse quality factor
        Area = (D + W)^2;
        G    = R / (omega * L)^2;
        invQ = R / (omega * L);
        
        % loop constraints
        Area <= 0.25e-6;
        W <= 30e-6;
        5e-6 <= W;
        10 * W <= D;
        D <= 100 * W;
        SRFSpec <= SRF;
        omegaSRF^2 * L * C <= 1;
        
        % ****************************************%
        % transistor definitions and constraints %
        % ****************************************%
        GM  = 6e-3 * (w / l)^0.6 * (Imax / 2)^(0.4);
        GD  = 4e-10 * (w / l)^0.4 * (Imax / 2)^(0.6) * 1 / l;
        Vgs = 0.34 + 1e-8 / l + 800 * (Imax * l / (2 * w))^0.7;
        Cgs = 1e-2 * w * l;
        Cgd = 1e-9 * w;
        Cdb = 1e-9 * w;
        
        % transistor constraints
        2e-6 <= w;
        0.13e-6 <= l;
        l <= 1e-6;
        
        % ***************************************************%
        % overall LC oscillator definitions and constraints %
        % ***************************************************%
        invVOsc = (G + GD) / IBias;
        
        % phase noise
        kT4  = 4 * 1.38e-23 * 300;
        kT4G = 2 * kT4;
        LoopCurrentNoise = kT4 * G;
        TransistorCurrentNoise = 0.5 * kT4G * GM;
        PN = 1 / (160 * (FOff * VOsc * CT)^2) * (LoopCurrentNoise + TransistorCurrentNoise);
        
        % capacitance
        Cfix = C + 0.5 * (CL + Cgs + Cdb + 4 * Cgd); % fixed capacitance
        CDiffMaxFreq = Cfix + 0.5 * Cvar;
        
        invLoopGain = (G + 0.5 * GD) / (0.5 * GM);
        
        % LC oscillator constraints
        PN <= PNSpec;
        omega^2 * L * CT == 1;
        omega^2 * (1 + T)^2 * L * CMaxFreq == 1;
        4 * T / ((1 - T^2)^2) * CT <= Csw * (1 + CvarCswLSBOverlap / CswSegs);
        Csw * CvarCswLSBOverlap / CswSegs <= 0.5 * Cvar * (CvarRatio - 1);
        CDiffMaxFreq <= CMaxFreq;
        VOsc + 2 * Vbias <= 2 * Vdd;
        VOsc * invVOsc <= 1;
        invLoopGain * LoopGainSpec <= 1; % loop gain spec
        Vbias + Vgs + IBias / 2 * R / 2 <= Vdd;  % bias constraint spec
        Imax == IBias;
cvx_end
