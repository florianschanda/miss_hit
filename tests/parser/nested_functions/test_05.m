% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function test_05
    x = 5;
    nestfun;

    function y = nestfun
        y = x + 1;
    end
end
