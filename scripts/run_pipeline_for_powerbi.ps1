
$ErrorActionPreference = "Stop"

$ProjectPath = "C:\Users\mjana\OneDrive\Desktop\CITYSENSE_AI"
$PythonPath = Join-Path $ProjectPath ".venv\Scripts\python.exe"
$PipelinePath = Join-Path $ProjectPath "scripts\run_citysense_pipeline.py"
$StatusPath = Join-Path $ProjectPath "data\processed\powerbi_pipeline_status.txt"
$RefreshCsvPath = Join-Path $ProjectPath "data\processed\powerbi_refresh_status.csv"

Set-Location $ProjectPath
New-Item -ItemType Directory -Force -Path (Split-Path $StatusPath) | Out-Null
Remove-Item $StatusPath -ErrorAction SilentlyContinue

& $PythonPath $PipelinePath
$PipelineExitCode = $LASTEXITCODE

$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

if ($PipelineExitCode -eq 0) {
    "SUCCESS $RunTime" | Set-Content -Path $StatusPath

    @"
pipeline_status,last_successful_refresh
SUCCESS,$RunTime
"@ | Set-Content -Path $RefreshCsvPath -Encoding UTF8
} else {
    "FAILED ExitCode=$PipelineExitCode $RunTime" |
        Set-Content -Path $StatusPath

    exit $PipelineExitCode
}
