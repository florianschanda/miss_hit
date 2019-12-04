% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% numeric matrix
function f (x = [0, 1, 2;3, 4, 5])
  assert (x == [0 1 2;3 4 5]);
end

function test()
 f()
end
