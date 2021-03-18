% (c) Copyright 2021 Florian Schanda

a = 42;
potato(a=5);
disp(a);

% Ahhhhh.
% * Octave prints '5' and '5'
% * MATLAB < 2021a errors out "The expression to the left of the
%   equals sign is not a valid target for an assignment."
% * MATLAB 2021a prints 'a', and '5', and '42'

% This is so comically bad, I don't even know where to start. I *did*
% warn MathWorks about this, but clearly they don't care.
