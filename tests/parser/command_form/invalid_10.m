% (c) Copyright 2019 Florian Schanda

function invalid_10()
  x = 5;
  x + 1  % ok, 6
  x+ 1   % ok, 6
  x+1    % ok, 6
  x +1   % fail, because command syntax and x is not a function
end
