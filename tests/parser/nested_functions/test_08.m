% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function test_08(x, y)              % Main function
  B(x,y)
  D(y)

  function B(x,y)            % Nested in A
    C(x)
    D(y)

    function C(x)           % Nested in B
      D(x)
    end
  end

  function D(x)              % Nested in A
    E(x)

    function E(x)           % Nested in D
      disp(x)
    end
  end
end
