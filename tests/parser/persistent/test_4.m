% From https://uk.mathworks.com/help/matlab/ref/persistent.html

% The declaration of a variable as persistent must precede any other
% references to the variable, including input or output arguments. For
% example, the persistent declarations in the following functions are
% invalid.

function myfunA(x)
    persistent x
end

function myfunB
    x = 0;
    persistent x
end
