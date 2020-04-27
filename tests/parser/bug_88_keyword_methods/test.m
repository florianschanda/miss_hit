% (c) Copyright 2020 Florian Schanda

c = cls();

disp(c.end());
disp(c.import());
disp(c.methods());

% Note that this overrides methods, which seems like a bad idea
disp(methods(c));

disp(c.properties());
disp(c.events());
disp(c.enumeration());
disp(c.arguments());

% The last one can be called using dynamic references
disp(c.('wibble.wabble')());
