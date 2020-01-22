% (c) Copyright 2019-2020 Zenuity AB

classdef miss_hit < handle

    properties (Constant, Access = private)

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

        function cached()
            % Run miss_hit on cached files in repository.

            files = git_retrieve_files('git --no-pager diff --name-only');
            miss_hit.run(files);

        end

        function lastCommit()
            % Run miss_hit on files changed in the last commit.

            files = git_retrieve_files( ...
                      'git --no-pager diff HEAD^ HEAD --name-only');
            miss_hit.run(files);

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

    methods (Static, Access = private)

        function run(file_or_folder)

            AssertFileOrFolder = @(f) ...
                assert(ischar(f) && (isfolder(f) || isfile(f)), ...
                       'Not a file or folder.');

            if iscell(file_or_folder)
                cellfun(AssertFileOrFolder, file_or_folder);
                file_or_folder = strjoin(file_or_folder);
            else
                AssertFileOrFolder(file_or_folder);
            end

            % Do the auto-fixes
            python_command = strjoin({ ...
                'cd', miss_hit.here, '&&', ...
                'python3', 'mh_style.py', file_or_folder, ...
                '--fix', '--no-style'});
            system(python_command, '-echo');

            % Generate report for remaining issues.
            report_name = fullfile(miss_hit.here, 'report.html');
            python_command = strjoin({ ...
                'cd', miss_hit.here, '&&', ...
                'python3', 'mh_style.py', file_or_folder, ...
                    '--html', report_name});
            system(python_command);

            web(report_name);

        end

    end

end

function files = git_retrieve_files(msg)

    fldr = cd();
    [s, m] = unix(strjoin({'cd', fldr, '&&', msg}));
    assert(s == 0, 'Could not execute git command.');

    f = strsplit(m);
    f(cellfun(@isempty, f)) = [];
    assert(~isempty(f), 'No files changed.');

    files = cellfun(@(e) fullfile(fldr, e), f, 'un', false)';

end
