% (c) Copyright 2019 Zenuity AB

%% ok

y = x(2, :)
y = x(3, 1:end)
y = x{:}
x = j:k
x = j:i:k
A(:)
A(j:k)

%% not ok

for i = 1 : 2
A(m,:)
A(:,n)
x = j : i : k
end
