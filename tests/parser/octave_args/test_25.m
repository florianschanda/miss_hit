% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% Function handle (builtin)
function f (x = @sin)
  finfo = functions (x);
  fname = finfo.function;
  assert (is_function_handle (x) && strcmp (fname == "sin"));
end

function test()
 f()
end
