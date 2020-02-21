% From https://uk.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

% A useful function syntax in MATLAB uses the public properties of a
% class for the names of name-value arguments. To specify name-value
% arguments for all settable properties defined by a class (that is,
% all properties with public SetAccess), use the following syntax in
% an arguments block.
%
% structName.?ClassName
%
% A function can use the "structName.?ClassName" syntax only once.

function test_1(x,y,propArgs)
    arguments
        x (:,:) double
        y (:,:) double
        propArgs.?matlab.graphics.chart.primitive.Bar
    end
    propertyCell = namedargs2cell(propArgs);
    bar(x,y,propertyCell{:});
end
