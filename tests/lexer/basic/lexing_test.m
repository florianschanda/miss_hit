%
% This is a comment, and then a newline

% This is a continuation
...
...   This is really a `comment'

% Identifier
potato
kitten99
miss_hit
p0tat0

% Number
1 1.1 .1
1.1e2
1.1e+2
1.1e-2

% Keyword
break case catch classdef continue else elseif end for function global
if otherwise parfor persistent return spmd switch try while

% Simple operators
< <= > >= == ~=
+ - * / ~ ^ \
& && | ||
.* ./ .\ .^ .'

% The transpose operator is special, since lexing is context sensitive
1'
potato''

% In a ' string '' is the single quote
'potato'''
[a, '''', b, ''',']

% Punctiation
,;:()[]{}
a.b
@?!

% Assignment
=

% Strings, again the single quote is super special
'potato'
''

% Some fun constructs that will make you really appreciate the language
[1+1]
[1 +1]
[1 + 1]
[1+ 1]
[1++1]
[1+++1]
['foo' '1]1' ]'

% cd is weird and needs special care
cd ../foo/_bar # potato?
mkdir __potato?
