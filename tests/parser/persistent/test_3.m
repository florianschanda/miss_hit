% From https://uk.mathworks.com/help/matlab/ref/persistent.html

% Since MATLAB initializes a persistent variable to an empty matrix
% ([]), typically functions check to see if a persistent variable is
% empty, and, if so, initialize it.

function myFun()
    persistent n
    if isempty(n)
        n = 0;
    end
    n = n+1;
end
