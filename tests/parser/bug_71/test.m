% (c) Copyright 2019 Florian Schanda

x = [1, 2, 3];
x([end-1 end]) = x([end end-1]);
assert(x == [1, 3, 2]);
