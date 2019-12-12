% From https://uk.mathworks.com/help/matlab/ref/persistent.html

function myFun()
    persistent n
    if isempty(n)
        n = 0;
    end
    n = n+1
end
