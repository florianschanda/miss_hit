% From https://www.mathworks.com/help/matlab/matlab_prog/nested-functions.html

function test_04
    nestedfun1;
    nestedfun2;

    function nestedfun1
        x = 1;
    end

    function nestedfun2
        x = 2;
    end
end
