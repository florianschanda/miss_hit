This tests shows a lexer bug that causes the test to be re-written to
```
x = [1 - [1]]
```
Which would produce 0 and not the correct result.
