% (c) Copyright 2019 Florian Schanda

% Curiously neither the MATLAB documentation nor Octave explicitly say
% what happens if you nest these.
%
% Octave says "between matching '#{' and '#}' or '%{' and '%}'
% markers." so that does imply some support for nesting.

% Actual behaviour:
%    MATLAB: <TODO>
%    Octave: 1 5

disp("1");
%{
  disp("2");
  %{
    disp("3");
  %}
  disp("4");
%}
disp("5");
