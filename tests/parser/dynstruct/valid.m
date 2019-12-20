function test_01()
  foo.x = 0;
  foo.y = 0;

  foo.('x') = 42;
  [foo.('x')] = 42;
end

function test_02()
  foo.x = 0;
  foo.y = 0;

  [foo.('x') foo.('y')] = potato();
end
