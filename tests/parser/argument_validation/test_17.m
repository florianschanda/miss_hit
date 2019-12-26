% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function test_17(width,height,options)
    arguments
        width double
        height double
        options.LineStyle (1,1) string = "-"
        options.LineWidth (1,1) {mustBeNumeric} = 1
    end

    % Function code

end
