function r = test_03(a, b, c, d)

    if (a | b) & (c | d)
        r = 'a';
    else
        r = 'b';
    end

end
