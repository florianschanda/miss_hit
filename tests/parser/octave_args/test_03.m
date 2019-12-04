% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% no inputs, one of multiple outputs
function [x, y] = f ()
  assert (nargin == 0);
  assert (nargout == 1);
  x = 2;
end

function test()
 assert (f () == 2);
end
