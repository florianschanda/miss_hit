function x = regression2
    persistent y z, if isempty(y), y = 42; end
    x = y;
end
