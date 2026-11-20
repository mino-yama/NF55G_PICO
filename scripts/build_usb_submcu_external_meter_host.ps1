param(
    [string]$Toolchain = "$env:LOCALAPPDATA/Arduino15/packages/rp2040/tools/pqt-gcc/4.1.0-1aec55e"
)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $taskRoot 'firmware/usb_submcu_external_meter_host'
$cmakeExe = Join-Path $taskRoot '.venv/Scripts/cmake.exe'
$ninjaExe = Join-Path $taskRoot '.venv/Scripts/ninja.exe'

foreach ($required in @($cmakeExe, $ninjaExe, (Join-Path $Toolchain 'bin/arm-none-eabi-gcc.exe'))) {
    if (-not (Test-Path $required)) { throw "Required build tool not found: $required" }
}

$cmakeArgs = @(
    '-S', $sourceDir,
    '-B', "$sourceDir/build",
    '-G', 'Ninja',
    "-DPICO_SDK_PATH=$taskRoot/tools/usb_submcu/pico-sdk-2.2.0",
    "-DPICO_TOOLCHAIN_PATH=$Toolchain",
    "-Dpioasm_DIR=$taskRoot/tools/usb_submcu/sdk-tools-2.2.0/pioasm",
    "-Dpicotool_DIR=$taskRoot/tools/usb_submcu/picotool-2.2.0/picotool",
    "-DCMAKE_MAKE_PROGRAM=$ninjaExe",
    '-DCMAKE_BUILD_TYPE=Release'
)

& $cmakeExe @cmakeArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $cmakeExe --build "$sourceDir/build" --parallel 8
exit $LASTEXITCODE