% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% Fully used varargin and varargout
function [varargout] = f (varargin)
  assert (nargin == 3);
  assert (nargout == 4);
  varargout{1} = varargin{1};
  varargout{2} = varargin{2};
  varargout{3} = varargin{3};
  varargout{4} = 4;
end

function test()
 [s, t, u, v] = f (1, 2, 3);
 assert ([s t u v] == [1 2 3 4]);
end
