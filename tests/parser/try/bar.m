% From https://uk.mathworks.com/help/matlab/ref/try.html

function bar()
    x = 5;
    y = 0;
    try
        z = x / y;
    catch ME
        rethrow(ME);
    end
end
