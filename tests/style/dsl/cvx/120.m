cvx_begin
    variable r(2*n-1,1) complex
    % minimize stopband attenuation
    minimize(max(real(As * r)))
    subject to
        % passband ripple constraints
        (10^(-ripple / 20))^2 <= real(Ap * r) <= (10^(+ripple / 20))^2;
        % nonnegative-real constraint for all frequencies
        % a bit redundant: the passband frequencies are already constrained
        real(A * r) >= 0;
        % auto-correlation symmetry constraints
        imag(r(n)) == 0;
        r(n - 1:-1:1) == conj(r(n + 1:end));
cvx_end
