% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% varargin and varargout with one output
function [x, varargout] = f (varargin)
  assert (nargin == 0);
  assert (nargout == 1);
  x = 2;
end

function test()
 assert (f () == 2);
end
