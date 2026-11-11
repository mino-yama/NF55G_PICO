# 既存の案件内SDKとツールだけを使い、USB単体確認FWを再ビルドする。
param(
    [string]$Toolchain = "$env:LOCALAPPDATA/Arduino15/packages/rp2040/tools/pqt-gcc/4.1.0-1aec55e"
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $taskRoot 'firmware/usb_submcu_acceptance'
$cmakeExe = Join-Path $taskRoot '.venv/Scripts/cmake.exe'
$cmakeArgs = @(
    '-S', $sourceDir, '-B', "$sourceDir/build", '-G', 'Ninja',
    "-DPICO_SDK_PATH=$taskRoot/tools/usb_submcu/pico-sdk-2.2.0",
    "-DPICO_TOOLCHAIN_PATH=$Toolchain",
    "-Dpicotool_DIR=$taskRoot/tools/usb_submcu/picotool-2.2.0/picotool",
    "-DCMAKE_MAKE_PROGRAM=$taskRoot/.venv/Scripts/ninja.exe",
    '-DCMAKE_BUILD_TYPE=Release'
)
& $cmakeExe @cmakeArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $cmakeExe --build "$sourceDir/build" --parallel 4
exit $LASTEXITCODE
