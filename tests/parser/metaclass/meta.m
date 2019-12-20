% Using
% https://www.mathworks.com/help/matlab/ref/metaclass.html

function [a, b] = test_01()
  a = ?potato;
  b = meta.class.fromName('potato');
end

function [mc] = test_02()
  mc = ?meta.class;
end
