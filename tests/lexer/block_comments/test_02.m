% (c) Copyright 2019 Florian Schanda

disp("foo");
%{ not valid
 disp("bar");
%}
disp("baz");
