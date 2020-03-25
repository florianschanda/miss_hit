% (c) Copyright 2020 Florian Schanda

for i = 1:10
    for j = 1:10
        disp(i * j);
    end
    if i + j > 10
        continue
    end
end
