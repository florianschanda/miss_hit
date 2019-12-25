% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function test_01
  disp('This is the parent function')
  nestedfx

  function nestedfx
    disp('This is the nested function')
  end
end
