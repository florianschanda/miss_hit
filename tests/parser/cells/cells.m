% Using
% https://www.mathworks.com/help/matlab/matlab_prog/create-a-cell-array.html
% https://www.mathworks.com/help/matlab/matlab_prog/add-cells-to-a-cell-array.html
% https://www.mathworks.com/help/matlab/matlab_prog/combining-cell-arrays-with-non-cell-arrays.html

function myCell = test_01()

  myCell = {1, 2, 3;
            'text', rand(5,10,2), {11; 22; 33}};

end

function C = test_02()
  C = {};
end

function C = test_03()
  C = {1, 2, 3};
  C{4, 4} = 44;
  C{5,5} = [];
end

function [C4, C5] = test_04()
  C1 = {1, 2, 3};
  C2 = {'A', 'B', 'C'};
  C3 = {10, 20, 30};

  C4 = [C1; C2; C3];
  % C4 =
  %   [ 1]    [ 2]    [ 3]
  %   'A'     'B'     'C'
  %   [10]    [20]    [30]

  C5 = {C1; C2; C3};
  % C5 =
  %   {1x3 cell}
  %   {1x3 cell}
  %   {1x3 cell}
end

function A = test_05()
  A = [100, {uint8(200), 300}, 'MATLAB'];
  % {100, 200, 300, 'MATLAB'}
end
