% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% multiple inputs, multiple outputs, but not all of either
% WARNING: The original test did not assign the outputs, it just
% requested them, and I think that is supposed to be an error.  It also
% still has a non-assigned output argument.
function [x, y, z] = f (a, b, c, d, e)
  assert (nargin == 4);
  assert (nargout == 2);
  x = a;
  y = b;
end

function test()
 [s, t] = f (1, 2, 3, 4);
 assert ([s t] == [1 2]);
end
