% (c) Copyright 2019 Florian Schanda

function test_01()
  a = 10 ^ 4;
  b = 10 ^ (-4);

  x = 10 ^ +4;   % x == a
  y = 10 ^ -4;   % x == b
  z = 10 ^ -+-+4;  % z == a
end
