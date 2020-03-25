% (c) Copyright 2020 Florian Schanda

a = rand() > 0.5;
b = rand() > 0.5;
c = rand() > 0.5;

tmp = a && b || c;
if tmp
    display potato;
end

tmp = a & b | c;
if tmp
    display potato;
end;
