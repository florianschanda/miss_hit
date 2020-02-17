% (c) Copyright 2020 Florian Schanda

for i = 1:10
    for j = 1:10
        if i < j
            break
        end
        disp(i * j);
    end
end

disp('end');
