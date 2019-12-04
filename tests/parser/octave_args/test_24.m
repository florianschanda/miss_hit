% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% char (string, double quotes, punctuation)
function f (x = "abc123`1234567890-=~!@#$%^&*()_+[]{}|;':\",./<>?\\")
  assert (x, "abc123`1234567890-=~!@#$%^&*()_+[]{}|;':\" == ./<>?\\");
end

function test()
 f()
end
