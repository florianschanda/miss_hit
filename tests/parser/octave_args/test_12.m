% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% numeric vector (spaces)
function f (x = [0 1 2])
  assert (x == [0 1 2]);
end

function test()
 f()
end
