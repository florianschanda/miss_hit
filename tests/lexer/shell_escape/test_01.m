% From https://www.mathworks.com/help/matlab/matlab_external/run-external-commands-scripts-and-programs.html
% From https://www.mathworks.com/help/matlab/matlab_external/shell-escape-functions.html

!vi yearlystats.m
!excel.exe &
!dir &
!echo $PATH

function y = garfield(a,b,q,r)
  save gardata a b q r
  !gareqn
  load gardata
end
