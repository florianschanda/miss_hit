% (c) Copyright 2019 Zenuity AB

function potato()
    a = 9;
    b = [4 5 6];

    x = [1]; % x == 1
    x

    x = [1, 2 -3 + 4    % 1 2 1
        0.1 +.1i .2     % .1 .1i .2
        a (3) b(3);];   % a 3 b(3)
    x

    [b(2)] = 10;

    b (2)    % 10
    [b(2)]   % 10
    [b (2)]  % [4 10 6 2]

end
