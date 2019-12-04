% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% numeric vector (range)
function f (x = 1:3)
  assert (x == 1:3);
end

function test()
 f()
end
