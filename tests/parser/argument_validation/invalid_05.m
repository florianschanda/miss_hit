% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

% However, you cannot refer to input variables not yet declared in an
% arguments block. For example, using this declaration for argument a
% in the previous function is not valid because b and c have not been
% declared yet.

function c = invalid_05(a,b,c)
    arguments
        a uint32 = b * c
        b uint32
        c uint32
    end

    % Function code
end
