% (c) Copyright 2020 Florian Schanda

a = rand() > 0.5;
b = rand() > 0.5;
c = rand() > 0.5;

if a && b || c
    disp potato;
end

% https://uk.mathworks.com/help/matlab/ref/logicaloperatorsshortcircuit.html
%
% When you use the element-wise & and | operators in the context of an
% if or while loop expression (and only in that context), they use
% short-circuiting to evaluate expressions.

if a & b | c
    disp potato;
end
