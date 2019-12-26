% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function c = test_26(a, b,c)
    arguments
        a uint32
        b uint32
        c uint32 = a .* b
    end

    % Function code
end
