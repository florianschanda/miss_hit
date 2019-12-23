% From https://www.mathworks.com/help/matlab/matlab_oop/specifying-properties.html

classdef Prop
   properties
      Prop1
      Prop2 = 'some text'
      Prop3 = sin(pi/12)
      Prop4 = containers.Map
      Prop5 (1,1) double {mustBePositive} = 1
   end
   properties (Access = private)
      Salary
      Password
   end
   methods
     function obj = set.Password(obj,pw)
       if numel(pw) < 7
         error('Password must have at least 7 characters')
       else
         obj.Password = pw;
       end
     end
     function o = getPropValue(obj,PropName)
       o = obj.(PropName);
     end
   end
end
