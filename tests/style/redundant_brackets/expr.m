%% (c) Copyright 2020 Florian Schanda

m = [1, 2, 3];

x = (1);

x = (1 + 2) * 3; % ok

x = ((1 + 2)) * 3;

x = foo((x + 1), 2);

x = [(1 + 1) + 2] % ok

x = [(1 +1) +1] % very important brackets

x = (a * b) + (b * c); % ok

x = m((2));

(x + 1);

% problematic cases

x = (1 + ...
     2 ...
    );

x = foo(1, ...
        (2));
