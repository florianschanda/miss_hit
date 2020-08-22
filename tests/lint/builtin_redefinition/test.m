% (c) Copyright 2019 Niklas Nylen
% (c) Copyright 2019 Florian Schanda

false = 0.01; % bad

x = pi, [true] = 42; % bad

[a, uint8, b(i)] = potato; % uint8 bad, but the i is ok

function x = pi() % bad
  x = 3;

  for i = [1, 2]  % tolerable
    i = x;  % no, for many reasons
  end
end
