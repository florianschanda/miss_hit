% (c) Copyright 2020 Zenuity AB

function a = foo (x)
    a = 0;

    if x > 1
        a = a + 1;
    end

    if x > 2
        a = a * 2;
    end

    if x > 3
        a = a + x;
    end
end
