% From https://www.mathworks.com/help/matlab/matlab_oop/events-and-listeners.html

classdef MyClass < handle
   events
      StateChange
   end

   methods
      function upDateUI(obj)
         notify(obj,'StateChange');
      end
   end
end
