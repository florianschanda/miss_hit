% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function test_06
    x = 5;
    z = nestfun;

    function y = nestfun
        y = x + 1;
    end
end
