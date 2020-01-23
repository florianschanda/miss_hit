% From https://www.mathworks.com/help/matlab/matlab_prog/function-argument-validation-1.html

x = 1.0;
y = 1.0;
minval = 0.0;
maxval = 5.0;

myFunction(x,y,maxval,minval);
myFunction(x,y,maxval);
myFunction(x,y);
