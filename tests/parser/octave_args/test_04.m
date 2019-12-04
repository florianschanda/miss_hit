% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% one of multiple inputs, one of multiple outputs
function [x, y] = f (a, b)
  assert (nargin == 1);
  assert (nargout == 1);
  x = a;
end

function test()
 assert (f (1) == 1);
end
