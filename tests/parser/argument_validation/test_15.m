% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

function result = test_15(NameValueArgs)
    arguments
        NameValueArgs.Name1
        NameValueArgs.Name2
    end

    % Function code
    result = NameValueArgs.Name1 * NameValueArgs.Name2;
end
