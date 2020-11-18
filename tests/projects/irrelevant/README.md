When using an entry-point, we should not pick up files from our path
that MATLAB wouldn't pick up either.

See:
* https://www.mathworks.com/help/matlab/matlab_env/files-and-folders-that-matlab-accesses.html
* https://www.mathworks.com/help/matlab/matlab_oop/organizing-classes-in-folders.html

Specifically if a subdirectory not starting with + or @ is in a
directory on the path, we do not consider it.
