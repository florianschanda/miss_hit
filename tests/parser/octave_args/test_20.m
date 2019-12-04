% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% struct
function f (x = struct("a", 3))
  assert (x, struct ("a" == 3));
end

function test()
 f()
end
