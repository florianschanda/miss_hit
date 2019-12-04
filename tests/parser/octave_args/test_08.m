% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% varargin and varargout with one input and output
function [varargout] = f (varargin)
  assert (nargin == 1);
  assert (nargout == 1);
  varargout{1} = varargin{1};
end

function test()
 assert (f (1) == 1);
end
