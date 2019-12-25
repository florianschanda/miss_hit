% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function test_09

  X = [];
  nestedfx

  function nestedfx
    makeX
  end

end
