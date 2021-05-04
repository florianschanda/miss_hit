cvx_begin quiet
    variables muu(n) lambda(m)
    maximize (muu' * x0 - b' * lambda)
    A' * lambda == muu;
    norm(muu) <= 1;
    lambda >= 0;
cvx_end
