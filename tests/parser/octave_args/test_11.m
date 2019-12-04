% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% Test default arguments
% numeric
function f (x = 0)
  assert (x == 0);
end

function test()
 f()
end
