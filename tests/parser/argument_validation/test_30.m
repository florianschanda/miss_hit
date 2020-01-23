% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function test_30(a, b)
    arguments
        a {mustBeA(a,'double'), mustBeDims(a,2)}
        b {mustBeSize(b,[5,3])}
    end

    % Function code
end

% Custom validator functions
function mustBeA(input,className)
    % Test for specific class
    if ~isa(input,className)
        error('Input must be of class double.');
    end
end

function mustBeSize(input,sizeDims)
    % Test for specific size
    if ~isequal(size(input),sizeDims)
        error(['Input must be of size ',num2str(sizeDims)]);
    end
end

function mustBeDims(input,numDims)
    % Test for number of dimensions
    if ~isequal(length(size(input)),numDims)
        error(['Input must have ',num2str(numDims),' dimensions.']);
    end
end
