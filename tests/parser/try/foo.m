% From https://uk.mathworks.com/help/matlab/ref/try.html

function foo()
    x = 5;
    y = 0;
    try
        z = x / y;
    catch
        z = 1;
    end
end
