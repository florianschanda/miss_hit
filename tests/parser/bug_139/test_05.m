a = false(1, 5);
b = true(1, 5);
c = true(1, 5);
a(2:3) = true;
b(3:4) = false;

if a && b && c
    disp("yes");
else
    disp("no");
end
