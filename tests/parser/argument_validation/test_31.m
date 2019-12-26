% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function result = test_31(a, b, c, namedargs)
    arguments
        a (1,1) double
        b (1,1) double
        c (1,1) double = 1
        namedargs.Format (1,:) char
    end

    % Function code
    switch nargin
        case  2
            result = a + b;
        case 3
            result = a^c + b^c;
    end
    if isfield(namedargs,'Format')
        format(namedargs.Format);
    end
end
