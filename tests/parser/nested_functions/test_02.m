% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function test_02
  x = 5;
  nestfun1

  function nestfun1
    x = x + 1;
  end
end
