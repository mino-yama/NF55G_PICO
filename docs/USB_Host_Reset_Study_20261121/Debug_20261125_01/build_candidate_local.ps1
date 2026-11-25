$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    throw 'Run build_candidate_local.ps1 as a file using & with its full path. Do not paste the script contents into the prompt.'
}
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$source = Join-Path $repo 'firmware/usb_submcu_external_meter_host'
$cmake = Join-Path $repo '.venv/Scripts/cmake.exe'
$ninja = Join-Path $repo '.venv/Scripts/ninja.exe'
$sdk = Join-Path $repo 'tools/usb_submcu/pico-sdk-2.2.0'
$pioasm = Join-Path $repo 'tools/usb_submcu/sdk-tools-2.2.0/pioasm'
$picotoolDir = Join-Path $repo 'tools/usb_submcu/picotool-2.2.0/picotool'
$picotool = Join-Path $picotoolDir 'picotool.exe'
$gcc = Join-Path $env:LOCALAPPDATA 'Arduino15/packages/rp2040/tools/pqt-gcc/4.1.0-1aec55e'
$target = 'usb_submcu_external_meter_relay'
$version = 'meter-host-relay-20261125.2'
$runName = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
# Keep GCC dependency paths below the Windows legacy path limit.
$build = Join-Path $repo "tmp/usb_host_build/$runName"
$output = Join-Path $PSScriptRoot "candidate_$runName"

function Invoke-LoggedNative {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$LogPath
    )

    # Redirect each native stream directly to a file.
    $stdoutPath = "$LogPath.stdout"
    $stderrPath = "$LogPath.stderr"
    $quotedArguments = foreach ($argument in $Arguments) {
        # Escape quotes and trailing backslashes for Windows argument parsing.
        '"' + (($argument -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"'
    }
    Write-Host "Running $([System.IO.Path]::GetFileName($Executable)). Live output: $stdoutPath and $stderrPath"
    $process = Start-Process -FilePath $Executable -ArgumentList ($quotedArguments -join ' ') `
        -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $lines = @(Get-Content -LiteralPath $stdoutPath, $stderrPath)
    Set-Content -LiteralPath $LogPath -Value $lines -Encoding utf8
    $lines
    if ($process.ExitCode -ne 0) {
        throw "Failed to run $Executable (exit=$($process.ExitCode)). See $LogPath"
    }
}

foreach ($required in @($cmake, $ninja, $sdk, $pioasm, $picotool, (Join-Path $gcc 'bin/arm-none-eabi-gcc.exe'))) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Build dependency missing: $required" }
}
New-Item -ItemType Directory -Path $output | Out-Null
$configureArgs = @('-S', $source, '-B', $build, '-G', 'Ninja',
    "-DCMAKE_MAKE_PROGRAM=$ninja", "-DPICO_SDK_PATH=$sdk", "-DPICO_TOOLCHAIN_PATH=$gcc",
    "-Dpioasm_DIR=$pioasm", "-Dpicotool_DIR=$picotoolDir", '-DCMAKE_BUILD_TYPE=Release')
Invoke-LoggedNative -Executable $cmake -Arguments $configureArgs -LogPath (Join-Path $output 'configure.log')
Invoke-LoggedNative -Executable $cmake -Arguments @('--build', $build, '--target', $target, '--parallel', '2') `
    -LogPath (Join-Path $output 'build.log')

$uf2 = Join-Path $build "$target.uf2"
$elf = Join-Path $build "$target.elf"
# Verify the program version in the UF2 file before packaging it.
$info = Invoke-LoggedNative -Executable $picotool -Arguments @('info', '-a', $uf2) `
    -LogPath (Join-Path $output 'uf2_info.log')
if (($info -join "`n") -notmatch [regex]::Escape($version)) {
    throw "Could not verify firmware version $version"
}
Copy-Item -LiteralPath $uf2, $elf -Destination $output
$files = foreach ($name in @("$target.uf2", "$target.elf")) {
    $file = Get-Item -LiteralPath (Join-Path $output $name)
    [ordered]@{ name = $name; bytes = $file.Length; sha256 = (Get-FileHash -LiteralPath $file.FullName).Hash }
}
[ordered]@{ version = $version; files = @($files) } | ConvertTo-Json -Depth 3 |
    Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8
Write-Output "Candidate verified: $output"
