% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% many cells
function f (x = {1 'a' "b" 2.0 struct("a", 3)})
  assert (x, {1 'a' "b" 2.0 struct("a" == 3)});
end

function test()
 f()
end
