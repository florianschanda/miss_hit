% (c) Copyright 2020 Florian Schanda

% This is a regression test showing a weird cornercase for
% indentation. The special comment used to be wrongly indented.

function test_04(a, b, c)
    if nargin > 2
      x = 1;
    end

    wibble(1, ...
	   [3]);

    % This comment is special

    x = 2;
end
