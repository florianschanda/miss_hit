function rv = Foo(a, b, c)
    %| pragma Justify(metric, "npath",
    %|                "Ignore for now. To be fixed in POT-123");
    rv = 0;
    if a
        rv = rv + 1;
    end
    if b
        rv = rv + 1;
    end
    if c
        rv = rv + 1;
    end
end
