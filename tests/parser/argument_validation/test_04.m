% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function test_04(x,v,method)
    arguments
        x (1,:) {mustBeNumeric,mustBeReal}
        v (1,:) {mustBeNumeric,mustBeReal,mustBeEqualSize(v,x)}
        method (1,:) char {mustBeMember(method,{'linear','cubic','spline'})} = 'linear'
    end

    % Function code
end

% Custom validation function
function mustBeEqualSize(a,b)
    % Test if a and b have equal size
    if ~isequal(size(a),size(b))
        error('Size of first input must equal size of second input')
    end
end
