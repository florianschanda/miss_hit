% (c) Copyright 2019 Florian Schanda

function test_02()
  x = 2 ^ -(-3) ^ -(-2);  % (2 ^ 3) ^ 2
  % and not 2 ^ -((-3) ^ -(-2)) which is something else
end
