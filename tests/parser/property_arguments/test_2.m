% From https://uk.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

x = [1,2,3;4,5,6];
y = x.^2;

test_1(x,y);

test_1(x,y,'FaceColor','magenta','BarLayout','grouped');
