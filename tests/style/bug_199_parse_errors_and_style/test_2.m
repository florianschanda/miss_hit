% Taken from issue #199 (by alvinseville7cf)

clear all;

n = 4;
x = [1 3 5 7]';
y = [2 2 4 4]';

for i = 1:n
    for j = 1:n
        X(i, j) = x(i)^(j - 1);
    end
end

a = X^(-1) * y;
disp(a)

f(2, a)
f(4, a)
f(6, a)

function z = f(x, a)
    n = size(a);
    sum = 0;

    for i = 1:1:n(1)
        sum = sum + a(i) * x^(i - 1);
    end

    z = sum;
end
