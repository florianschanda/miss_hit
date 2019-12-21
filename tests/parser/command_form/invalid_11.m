% (c) Copyright 2019 Florian Schanda

function invalid_11()
  x = @(arg) arg;
  x + 1  %
  x+ 1   %
  x+1    % all fail because function handle + 1 doesn't work
  x +1   % fail, because you can't use lambda function in command form
end
