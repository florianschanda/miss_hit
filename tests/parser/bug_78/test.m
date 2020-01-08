% (c) Copyright 2020 Florian Schanda

disp f)oo % bar  % 'f)oo'
disp f)oo bar    % 'f)oo bar'
disp f(o,o)      % 'f(o,o)'
disp f(o, oo)    % 'f(o, oo)'
disp f(o[ b      % 'f(o[ b'
disp f] oo       % 'f] oo'
disp f]f[[ bar   % 'f]f[[ bar'
disp foo(%bar    % 'foo('
disp ]foo        % ']foo'
disp }foo        % '}foo'
d2 foo )foo      % 'foo' ')foo'
