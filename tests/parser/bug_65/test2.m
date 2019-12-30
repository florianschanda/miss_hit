% (c) Copyright 2019 Florian Schanda

tmp = test(12);

function x = test(potato)
   x = foo() + 1;

function y = foo()
   y = 12 + bar();
end

function z = bar()
   z = 1;
