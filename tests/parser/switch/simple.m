% From the MathWorks website

function simple()
    switch n
        case -1
            disp('negative one');
        case 0
            disp('zero');
        case 1
            disp('positive one');
        otherwise
            disp('other value');
    end
end
