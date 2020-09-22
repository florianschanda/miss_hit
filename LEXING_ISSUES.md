# Lexing issues of MATLAB

Lexing of MATLAB looks easy enough at first, but there are many
language feature that make a traditional approach (Dragon style
lexing + parsing) impossible.

This file attempts to document these, so that others don't make the
same mistakes (e.g. "trust me, it's easy, I'll just write a flex lexer
and fix some stuff afterwards").

## No official grammar

Doesn't exist. This is the first hurdle.

## Command form

A function without outputs that takes string arguments such as "disp"
or "clear" is normally called like this:

```
disp('Potato!');
```

However, you may omit the brackets (and optionally the quotation):

```
disp Potato!
```

This is called command form, and requires special treatment in the
lexer. For example `\` is not a valid character to appear in MATLAB
program text, but you can write:

```
cd C:\potato
```

So, we need to have special rules to detect command form. Thankfully
this got a bit easier in a recent MATLAB release and
[it is documented](https://uk.mathworks.com/help/matlab/matlab_prog/command-vs-function-syntax.html).

### Command form bracketing

If command form wasn't weird enough already, there are some surprising
properties involving brackets. They are classed into two: opening
`({[`, and closing `)}]`. If there is an imbalance, whitespace is
included in the string lexed.

For example this should lex as IDENT(foo) CARRAY(`bar`) CARRAY(`baz`):
```
foo bar baz % potato
```

However, this should lex as IDENT(foo) CARRAY(`b)ar baz `). Please
note the trailing whitespace here, its intentional.

```
foo b)ar baz % potato
```

### Command form quotation

To add to this, you can single-quote strings in command form, and they
disappear.

For example this again lexes as IDENT(foo) CARRAY(`bar`) CARRAY(`baz`):
```
foo 'bar' baz % potato
```

Imbalanced strings create lex errors:
```
foo 'bar baz % potato
    ^ error here
```

Quotations without separating whitespace are concatenated into
whatever is lexed. For example this lexes as IDENT(foo)
CARRAY(`barbaz`). Note no quotations here.
```
foo bar'baz'
```

The creates counter-intuitive things like:
```
foo a' 'b  % actually a single CARRAY 'a b'
```

A double single quote can be used to include a single quote:
```
foo pot''''ato % pot'ato
```

Finally, this does not work with double-quotes. The following lexes as
IDENT(foo) CARRAY(`"bar"`). Note the double-quotes are part of the
single-quoted string.
```
foo "bar"
```

### Continuations in command form

The final cherry on top is that continuations can appear in command
forms as well, and they carry on to the next line. This lexes as
IDENT(foo) CARRAY(`bar`) CONTINUATION CARRAY(`baz`).
```
foo bar ...
    baz
```

However, continuations are not allowed to be the first thing in a
command-form. This lexes as IDENT(foo) CONTINUATION IDENT(bar)
CONTINUATION IDENT(baz).
```
foo ...
    bar ...
    baz
```

## Numbers

The allowed syntax for numbers is extremely free, which creates
ambiguities that need to be manually resolved. For example the
following are all valid number tokens:
```
1
2.0
3.
.4
```

In a classic lexer, this would create an ambiguity for this:
```
1.1.1
```

In older versions of MATLAB (R) this used to parse, but now thankfully
it doesn't. But you still need to add a special error checking for
number lexing to raise an error in this specific case.

Also note that the `./` operator (and the other 4 operators that start
with a '.') create an ambiguity here. The following expression:
```
x = 1./b
```

In MATLAB and Octave this appears to be resolved by giving the `./`
higher precedence, so the individual tokens here should be `1`, `./`,
and `b`.

## Single-quoted strings

The single quote has two meanings. It can either be a transpose
operation (e.g. `a'` or a character array (e.g. `'foo'`). It also
means some expressions need intermediate values. For example the
following cannot be simplified to `y = 'foo'';`:
```
x = 'foo';
y = x';
```

The rules as to when a `'` introduces a string are complex and depend
on the *previously lexed token* and *whitespace before this
token*. The following rules are given in order of precedence:

If there is preceding whitespace or we're the first token on the
current line then we're always a CARRAY:
```
'foo'
x = 'foo'
x = [a' 'foo']
```

If the last token is an identifier, number, transpose
operator, or any closing bracket then we deal with a transpose
operator.
```
x = y';
y = 1'';
z = 1.''.';
w = size(1)';
```

Otherwise we have a character array.

## Matrices

MATLAB (R) features very user friendly ways to write matrices, but
they are painful to parse and lex correctly. Inside matrices
whitespace matters. The lexer needs to keep track of all brackets so
that it can always know if we're inside a matrix (or cell) or not.

The canonical way to write a 2x2 identity matrix is this:
```
m = [1, 0; 0, 1];
```

However there are many ways this can be written:
```
m = [1 0
     0 1];
```

Or perhaps:
```
m = [1,0;;;
% potato
  ,0 1,;];
```

Rows are separated by either `;` or a newline. Items on each row are
separated by whitespace or commas, or both. Unfortunately this leads
to trouble:
```
m = [+1 +0
     + 0 +1 + 0];
```

Why is the final `+0` added to the `+1`? Why is it not its own element
creating a malformed matrix? Or even worse:
```
x = [1 + 1]  % this is [2]
y = [1 ++ 1] % this is [1 1]
z = [1 +++ 1] % this is also [1 1]
```

As this depends on whitespace, to deal with this in the parser we have
decided to add anonymous commas in the lexer. So the parser sees the
following instead:

```
m = [+1, +0
     + 0, +1 + 0];
x = [1 + 1]  % this is [2]
y = [1, ++ 1] % this is [1 1]
z = [1, +++ 1] % this is also [1 1]
```

The rules when to add such a comma are probably the single most
complex feature of the lexer.

First we need to find the first two character after any
whitespace. Following the `1` in x, this would be `+ ` and for y it
would be `++`. Note that this search must also correctly skip line
continuations.

Second, commas can only appear after some tokens. Specifically
identifiers, numbers, char arrays or strings, closing brackets, the
'end' keyword or transpose operations.

Third, we never add commas if no whitespace follows the current token.

So if we have whitespace, the previous token is relevant, and the next
characters exists and is not `*/\^<>^|=.:!` (indicating a binary
operation) but is not `.NUMBER`, or the next two characters are not
`==` (again indicating a binary operation) then maybe we need to add a
comma. In order of precedence, based on the next non-whitespace
character:

No comma in these situations:
* `,`, `;`, newline
* `%` (and `#` for octave)

Add an anonymous comma in these situations:
* any alphanumeric character
* `'` or `"`
* any opening bracket
* `@` or `?`
* `.` (it must be a number literal)
* `-` or `+` or `~` and the character after is also `+` or `-` or `(`
* `-` or `+` or `~` and the character after is alphanumeric

Do not add a comma otherwise.

### Lambda functions

There is one more exception to these already confusing rules, and
these are lambda functions. If we are after a closing bracket of a
lambda parameter list, then no comma is inserted:

```
x = {@(x) 12};
```

### Assignment targets

Assignment targets look like matrices, but they are not. Many things
that are permitted in a matrix are not valid in an assignment
target. For example the following is not valid:
```
[x; y] = size(1)';
```

Hence the lexer should distinguish between a matrix and assignment
targets. This essentially involves looking ahead matching brackets to
find the first non-whitespace character following the closing `]`. If
it is a `=` then we deal with an assignment target, if not then it
must be a matrix.

This look-ahead is not easy, since strings can appear legitimately. For
example:
```
[x.('fo)o')] = 10;
```

While this is not semantically legal (field names cannot have
brackets) it should be lexed correctly.

## Identifiers and Keywords

Classic dragon-style lexing and parsing benefits greatly from having
keywords. But what is a keyword in MATLAB (R)? It depends on the
context, and it is highly malleable.

The documentation gives us a list via the `iskeyword` function,
listing e.g. `if`, `else`, and `end`.

However the following is legal:
```
x = struct()
x.end = 12;
```

In lexing terms, if the previous token was a selection token (`.`)
then the following token is always an identifier.

Having a function named `end` is also legal if the function is a class
method. I am not sure yet how to deal with this, so for now MISS_HIT
does not allow it.

`~` is an operator, but it can be a legal identifier in an assignment
target (to indicate "don't care"):
```
[~, x] = size(1);
```

In lexing terms, we have decided to keep it as an operator, but have a
special rule in the parser rule for identifier that allows the `~` in
some cases. A similar rule exists for `end` to allow the following
expressions:
```
y = x(1:end, end-1:end-1);
```

Some keywords are keywords only in some contexts. Specifically
`classdef` introduces `properties`, `enumeration`, `events`, and
`methods` as keywords. The `methods` block removes this limitation
again. Hence you can have a method called `properties`, but not a
property called `properties`.

Since 2019b the `function` keyword makes `arguments` become a keyword
in the top-level block.
```
function potato(x)
   arguments % keyword
      x uint
   end
   try
      arguments = 12; % identifier
   end
   arguments = 42; % keyword again not allowed in MISS_HIT
```

### Interaction with command form
Note that keeping track of block is essential anyway, since the
argument validation `x uint` would normally be lexed as
command-form. But inside `properties`, `events`, `enumeration`, and
`arguments` blocks the command-form detection is always turned off.

## Block comments

Block comments can be nested (this is not document officially). The
following will print 1 and 5:

```
disp 1
%{
disp 2
%{
disp 3
%}
disp 4
%}
disp 5
```

If any text appears before or after the `%{` or `%}` the block comment
is ignored. For example this will print 1 2 4 5.

```
disp 1 %{
disp 2
%{
disp 3
%}
disp 4
%}
disp 5
```

MISS_HIT will emit warnings about comments that contain `%{` and `%}`
unless they are proper block comments.

## Unicode

While unicode is not permitted in identifiers, it is permitted in
program texts and literals. This can lead to surprising programs:

```
potato foo bar ٪ This will print foo and bar
function potato(varargin)
    for i = 1:nargin
        disp(varargin{i});
    end
end
```

Here we have a clever use of the arabic percent `٪`. This is not `%`,
which starts a comment. Instead we print:

```
foo
bar
٪
This
will
print
foo
and
bar
```

If the `٪` is a `%` then the program would only print:

```
foo
bar
```
