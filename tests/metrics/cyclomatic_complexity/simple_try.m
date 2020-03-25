% (c) Copyright 2020 Florian Schanda

try
    disp 1;
    maybe_exception;
    disp 2;
    maybe_exception;
    disp 3;
    maybe_exception;
    disp 4;
catch
    disp 5;
end
