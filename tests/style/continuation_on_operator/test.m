% (c) Copyright 2019 Niklas Nylen

% Desired syntax:
x = a + b + ...
    c + d;
x = (a || b) && ...
    (c || d);

% OK (but requries parsing):
x = a + b + ...
    -c + d;

% Undesired syntax:
x = a + b ...
    + c + d;
x = (a || b) ...
    && (c || d);