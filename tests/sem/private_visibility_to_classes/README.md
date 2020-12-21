Test to demonstrate visibility for private functions: a class file can make
use of them, but only if the class file is in the directory containing the
private directory.

A class file in a @ directory cannot see it anymore: so calling the
constructor in test_b should result in an error.
