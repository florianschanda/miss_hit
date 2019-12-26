% (c) Copyright 2019 Florian Schanda

function r = test_01(x, y)
  arguments
    x (1, 1) single {mustBePositive, mustBeFinite}
    y (1, 1) single
  end

  r = 0.5 * x + 0.5 * y
end
