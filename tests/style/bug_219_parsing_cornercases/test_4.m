% Taken from https://github.com/spm/spm12

switch dimord
    case 'chans_samples'
        for i=1:length(scaling)
            dat(i,:) = scaling(i) .* dat(i,:);
        end
    case'chans_samples_trials'
        for i=1:length(scaling)
            dat(i,:,:) = scaling(i) .* dat(i,:,:);
        end
    otherwise
        ft_error('unexpected dimord');
end % switch
