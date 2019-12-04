% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% no input or output arguments
function f ()
  assert (nargin == 0);
  assert (nargout == 0);
end

function test()
 f;
end
