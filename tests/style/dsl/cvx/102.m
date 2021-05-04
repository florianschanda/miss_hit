cvx_begin quiet
    variable c(M,1)
    variable d(N-1,1)
    
    % feasibility problem
    % passband constraints
    (Ap_num * c) <= (10^(+delta / 20))^2 * (Ap_den * [1; d]); % upper constr
    (Ap_num * c) >= (10^(-delta / 20))^2 * (Ap_den * [1; d]); % lower constr
    % stopband constraint
    (As_num * c) <= (Us_cur) * (As_den * [1; d]); % upper constr
    % nonnegative-real constraint
    Anum * c >= 0;
    Aden * [1; d] >= 0;
cvx_end
