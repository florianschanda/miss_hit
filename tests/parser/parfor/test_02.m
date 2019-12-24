% (c) Copyright 2019 Florian Schanda

function test_02(x)
  parfor (i = 1:x, 8)
    disp(i);
  end
end
