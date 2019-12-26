% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function test_03(a,b,c)
    arguments
        a double
        b char
        c SpeedEnum
    end

    % Function code
    disp(class(a))
    disp(class(b))
    disp(class(c))
end
