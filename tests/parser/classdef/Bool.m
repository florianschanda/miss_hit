% From https://www.mathworks.com/help/matlab/matlab_oop/enumerations.html

classdef Bool < logical
   enumeration
      No  (0)
      Yes (1)
   end
   methods
     function obj = Bool(val)
       obj@logical(val);
     end
   end
end
