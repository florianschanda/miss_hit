% (c) Copyright 2020 Florian Schanda

a = rand() > 0.5;
b = rand() > 0.5;

tmp_1 = a & b;  % normal and

if a & b        % short-circuit, because used in an if
    tmp_2 = 1;
else
    tmp_2 = 0;
end

while a & b     % short-circuit, because used in a while
    a = 0;
end
