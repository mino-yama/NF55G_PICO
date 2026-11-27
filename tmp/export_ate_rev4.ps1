$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\m_yamada\OneDrive\My Document\NF55G\NF55G_Pico'
$inputDoc = Join-Path $taskRoot 'docs\ATE_Command_List_for_Test_Program_Rev4_20261126.docx'
$pdfTarget = Join-Path $taskRoot 'tmp\ate_rev4_render\ate_rev4.pdf'
New-Item -ItemType Directory -Path (Split-Path $pdfTarget) -Force | Out-Null
$wordTask = $null
$docTask = $null
try {
    $wordTask = New-Object -ComObject Word.Application
    $wordTask.Visible = $false
    $wordTask.DisplayAlerts = 0
    $docTask = $wordTask.Documents.Open($inputDoc, $false, $true)
    $docTask.ExportAsFixedFormat($pdfTarget, 17)
    Write-Output $pdfTarget
} finally {
    if ($null -ne $docTask) { $docTask.Close(0) }
    if ($null -ne $wordTask) { $wordTask.Quit() }
}
