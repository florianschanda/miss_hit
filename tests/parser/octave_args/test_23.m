% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% char (string, double quotes)
function f (x = "abc123")
  assert (x == "abc123");
end

function test()
 f()
end
