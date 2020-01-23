% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function p = test_07(a,b,c)
    p = @parabola;

    function y = parabola(x)
        y = a*x.^2 + b*x + c;
    end

end
