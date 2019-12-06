classdef miss_hit < handle

    properties (Constant, Access=private)

        here = fileparts(mfilename('fullpath'));

    end

    methods (Static)

        function init()
        end

        function currentFile()
            % Run miss_hit on the currently opened file.

            doc = matlab.desktop.editor.getActive();
            assert(doc.Editable, 'File is not editable.');
            assert(~doc.Modified, 'Save file before you proceed.');

            miss_hit.file(doc.Filename);

            matlab.desktop.editor.openDocument(doc.Filename);

        end

        function file(file)
            % Run miss_hit on given file.

            miss_hit.run(file);

        end

        function currentFolder()
            % Run miss_hit on the current folder.

            miss_hit.folder(cd());

        end

        function folder(folder)
            % Run miss_hit on the given folder.

            miss_hit.run(folder);

        end

    end

    methods (Static, Access=private)

        function run(file_or_folder)

            assert(ischar(file_or_folder) && ...
                (isfolder(file_or_folder) || isfile(file_or_folder)), ...
                'Input has to be a file or folder.');

            % Do the auto-fixes
            python_command = strjoin({ ...
                'cd', miss_hit.here, '&&', ...
                'python', 'mh_style.py', file_or_folder, '--fix', '--no-style'});
            system(python_command, '-echo');

            % Generate report for remaining issues.
            report_name = fullfile(miss_hit.here, 'report.html');
            python_command = strjoin({ ...
                'cd', miss_hit.here, '&&', ...
                'python', 'mh_style.py', file_or_folder, ...
                    '--html', report_name});
            system(python_command);

            web(report_name);

        end

    end

end
