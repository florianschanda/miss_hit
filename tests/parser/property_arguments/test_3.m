% From https://uk.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

% You can override the class property validation by redefining the
% property name with a specific name-value argument in the arguments
% block.
%
% structName.?ClassName
% structName.PropertyName (dim1,dim2,...) ClassName {fcn1,fcn2,...}
%
% The specific name-value argument validation overrides the validation
% defined by class for the individually specified property name.

% For example, the following function defines name-value arguments as
% the properties of the matlab.graphics.chart.primitive.Bar
% class. Also, it overrides the property name FaceColor to allow only
% these specific values: 'red', or 'blue'.

function test_3(x,y,propArgs)
    arguments
        x (:,:) double
        y (:,:) double
        propArgs.?matlab.graphics.chart.primitive.Bar
        propArgs.FaceColor {mustBeMember(propArgs.FaceColor,{'red','blue'})} = "blue"
    end
    propertyCell = namedargs2cell(propArgs);
    bar(x,y,propertyCell{:});
end
