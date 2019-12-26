% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function test_05(x,y,maxval,minval)
    arguments
        x (1,:) double
        y (1,:) double
        maxval (1,1) double = max(max(x),max(y))
        minval (1,1) double = min(min(x),min(y))
    end

    % Function code
end
