% Example taken from the 2021a release notes

myFunction(a,(name=value));

% The name=value syntax can only be used directly in function
% calls. They cannot be wrapped in a cell array or additional
% parentheses. So this should raise an error.
