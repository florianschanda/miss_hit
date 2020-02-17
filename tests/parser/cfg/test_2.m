% (c) Copyright 2020 Florian Schanda

for i = 1:5
  x = i;
end

for i = 1:5
  for j = 1:10
    x = i;
    w = j;
  end
  z = i + j;
end
