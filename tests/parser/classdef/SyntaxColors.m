% From https://www.mathworks.com/help/matlab/matlab_oop/enumerations.html

classdef SyntaxColors
   properties
      R
      G
      B
   end
   methods
      function c = SyntaxColors(r, g, b)
         c.R = r;
         c.G = g;
         c.B = b;
      end
   end
   enumeration
      Error   (1, 0, 0)
      Comment (0, 1, 0)
      Keyword (0, 0, 1)
      String  (1, 0, 1)
   end
end
