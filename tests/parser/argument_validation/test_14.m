% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

% Using varargin with functions that use argument validation is not
% recommended. If you use varargin to support legacy code, it must be
% the only argument in a Repeating arguments block.

% If varargin is restricted in size or class in the repeating
% arguments block, then the restrictions apply to all values in
% varargin.

% For example, this function defines two required positional arguments
% and varargin as the repeating argument.

function test_14(a, b, varargin)
    arguments
        a uint32
        b uint32
    end
    arguments (Repeating)
        varargin
    end

    % Function code
end
