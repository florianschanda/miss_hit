[CmdletBinding()]
param (
    [switch]$PreCommitChecks,
    [switch]$Copyright,
    [switch]$Doc,
    [switch]$Test,
    [switch]$Lint,
    [switch]$Style
)


$AllParams =@($PreCommitChecks, $Copyright, $Doc, $Test, $Lint, $Style)

if ($AllParams -notcontains $true) {
    $Doc = $true
    $Test = $true
    $Lint = $true
    $Style = $true
}

if ($Lint) {
    $Style = $true
}

if ($PreCommitChecks) {
    $Copyright = $true
    $Doc = $true
    $Test = $true
    $Lint = $true
}

$ErrorActionPreference = "Stop"

if ($Copyright) {
    python hook_scripts\copyright_year.py
}

if ($Doc) {
    Push-Location util
    python update_docs.py
    python update_versions.py
    Pop-Location
}

if ($Test) {
    Push-Location tests
    python run.py
    Pop-Location
}

if ($Style) {
    python -m pycodestyle miss_hit_core miss_hit mh_bmc mh_copyright mh_debug_enumerate_simulink_blocks mh_debug_parser mh_diff mh_lint mh_metric mh_sl_unpack mh_style mh_trace
}

if ($Lint) {
    python -m pylint --rcfile=pylint3.cfg --reports=no miss_hit_core miss_hit mh_bmc mh_copyright mh_debug_enumerate_simulink_blocks mh_debug_parser mh_diff mh_lint mh_metric mh_sl_unpack mh_style mh_trace
}

if ($Package) {
    git clean -xdf
    Copy-Item -Path setup_gpl.py -Destination setup.py
    New-Item -Path "miss_hit_core/resources/assets" -ItemType Directory
    Copy-Item -Path docs/style.css -Destination miss_hit_core/resources
    Copy-Item -Path docs/assets/* -Destination miss_hit_core/resources/assets
    python setup.py sdist bdist_wheel
    Remove-Item -Path "miss_hit_core/resources" -Recurse
    Copy-Item -Path setup_agpl.py -Destination setup.py
    python setup.py sdist bdist_wheel
    Remove-Item -Path setup.py
}
