% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% empty cell
function f (x = {})
  assert (x == {});
end

function test()
 f()
end
