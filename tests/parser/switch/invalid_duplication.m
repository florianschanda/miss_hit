% (c) Copyright 2019 Florian Schanda
% May require semantic analysis to check

switch potato
   case 1
      x = 1;
   case 2
      x = 2;
   case 1
      x = 3;
   case {2, 3, 4}
      x = 4;
end
