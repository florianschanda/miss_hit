Test to show that visibility of functions in private directories are
not shared in a package, despite what the documentation implies.

The call in Func_2 is not legal, since there is no visiblity of the
private function since it's in a different directory, even though its
in the same package (foo).
