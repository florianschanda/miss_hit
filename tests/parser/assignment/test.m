% Inspired by the 1999 Technical Report

function test_01()

  a(1:2:3,1:3) = 2;
  % 2   2   2
  % 0   0   0
  % 2   2   2

end

function test_02()

  [a(1:2:3,1:3)] = 2;
  % 2   2   2
  % 0   0   0
  % 2   2   2

end

function test_03()

  [a b] = size(1);

end
