function y = test_1 (x)
    %% ok
    if x
        y = 1;
    end

    if x
        y = y + 1;
    end
end

function y = test_2 (x)
    %% exceedes metric
    if x
        y = 1;
    end

    if x
        y = y + 1;
    end

    if x
        y = y + 1;
    end
end
