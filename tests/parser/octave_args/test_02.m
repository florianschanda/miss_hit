% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% one input with two possible inputs
function f (x, y)
  assert (nargin == 1);
  assert (nargout == 0);
end

function test()
 f (1);
end
