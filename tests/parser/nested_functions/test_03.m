% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function test_03
    nestfun2;

    function nestfun2
        x = 5;
    end

    x = x + 1;
end
