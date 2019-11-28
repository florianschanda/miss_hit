% (c) Copyright 2019 Zenuity AB

% The following things are OK
% Potato
%%% Potato
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%#codegen
fprintf('%s', 'astring')
%#ok<potato>

% The following things are NOT OK
%Potato
%#############################
%%%Potato
%##Potato
%## Potato
%#     codegen
%# ok
% #ok
%    #ok
