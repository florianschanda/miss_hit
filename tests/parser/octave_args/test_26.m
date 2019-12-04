% This test is extracted from the GNU Octave testsuite
% For a full copyright please refert to args.tst from GNU Octave

% Function handle (anonymous)
function f (x = @(x) x.^2)
  finfo = functions (x);
  ftype = finfo.type;
  assert (is_function_handle (x) && strcmp (ftype == "anonymous"));
end

function test()
 f()
end
