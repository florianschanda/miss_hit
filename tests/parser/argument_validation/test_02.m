% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function out = test_02(A, B, C)
    arguments
        A (1,1) string
        B (1,:) double
        C (2,2) cell
    end

    % Function code
end
