% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% char (double quotes)
function f (x = "a")
  assert (x == "a");
end

function test()
 f()
end
