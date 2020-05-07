function r = test_02(a, b, c, d)

    if [a | b, b & c] == [b | c, c & d]
        r = 'a';
    else
        r = 'b';
    end

end
