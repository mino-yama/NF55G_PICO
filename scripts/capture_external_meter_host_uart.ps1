param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^COM[0-9]+$')]
    [string]$Port,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$OutputPath,

    [ValidateRange(1, 3600)]
    [int]$DurationSeconds = 20
)

$ErrorActionPreference = 'Stop'
$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory -and -not (Test-Path $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}
if (Test-Path $OutputPath) {
    throw "Refusing to overwrite existing capture: $OutputPath"
}

$serial = [System.IO.Ports.SerialPort]::new(
    $Port,
    115200,
    [System.IO.Ports.Parity]::None,
    8,
    [System.IO.Ports.StopBits]::One
)
$serial.Handshake = [System.IO.Ports.Handshake]::None
$serial.ReadTimeout = 100
$serial.WriteTimeout = 100
$serial.DtrEnable = $false
$serial.RtsEnable = $false

$capture = $null
$byteCount = 0
try {
    $serial.Open()
    $capture = [System.IO.File]::Open(
        $OutputPath,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    $buffer = New-Object byte[] 256
    $clock = [System.Diagnostics.Stopwatch]::StartNew()

    while ($clock.Elapsed.TotalSeconds -lt $DurationSeconds) {
        try {
            $count = $serial.Read($buffer, 0, $buffer.Length)
            if ($count -gt 0) {
                $capture.Write($buffer, 0, $count)
                $byteCount += $count
            }
        } catch [System.TimeoutException] {
        }
    }

    $capture.Flush()
} finally {
    if ($capture) { $capture.Dispose() }
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose()
}

$hash = (Get-FileHash -Path $OutputPath -Algorithm SHA256).Hash
[PSCustomObject]@{
    Port = $Port
    Settings = '115200 8N1, no flow control, DTR/RTS off, TX unused'
    DurationSeconds = $DurationSeconds
    Bytes = $byteCount
    Sha256 = $hash
    Capture = (Resolve-Path $OutputPath).Path
} | Format-List