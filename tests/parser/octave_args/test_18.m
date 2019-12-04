% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% full cell
function f (x = {1})
  assert (x == {1});
end

function test()
 f()
end
