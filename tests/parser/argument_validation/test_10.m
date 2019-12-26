% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function [xCell,yCell,optionCell] = test_10(x,y,option)
    arguments (Repeating)
        x double
        y double
        option {mustBeMember(option,["linear","cubic"])}
    end

    % Function code
    % Return cell arrays
    xCell = x;
    yCell = y;
    optionCell = option;
end
