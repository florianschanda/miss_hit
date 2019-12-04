% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% varargin and varargout with no inputs or outputs
function [varargout] = f (varargin)
  assert (nargin == 0);
  assert (nargout == 0);
end

function test()
 f;
end
