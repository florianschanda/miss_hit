% From https://uk.mathworks.com/help/matlab/matlab_prog/anonymous-functions.html

function multiple()
    g = @(c) (integral(@(x) (x.^2 + c*x + 1),0,1));
end

function no_inputs()
    t = @() datestr(now);
    d = t();
end

function arrays()
    f = {@(x)x.^2;
         @(y)y+10;
         @(x,y)x.^2+y+10};
    f = {@(x) (x.^2);
         @(y) (y + 10);
         @(x,y) (x.^2 + y + 10)};

    x = f{1}(x);
    y = f{2}(y);
    z = f{3}(x,y);
end

function bad_arrays()
    f = {@(x) x.^2;
         @(y) y + 10;
         @(x,y) x.^2 + y + 10};
end
