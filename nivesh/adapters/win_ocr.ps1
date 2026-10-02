param (
    [Parameter(Mandatory=$true)]
    [string]$ImagePath
)

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
    }[0]

    function Await($WinRtTask, $ResultType) {
        $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
        $netTask = $asTask.Invoke($null, @($WinRtTask))
        $netTask.Wait(-1) | Out-Null
        $netTask.Result
    }

    [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
    [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
    [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null

    $resolved = (Resolve-Path $ImagePath).Path
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($resolved)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if ($null -eq $engine) {
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))
    }
    
    if ($null -eq $engine) {
        Write-Output '{"success": false, "error": "No OCR language engine available"}'
        exit 0
    }

    $ocrResult = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    $lines = @()
    foreach ($line in $ocrResult.Lines) {
        $lines += $line.Text
    }
    $text = $ocrResult.Text

    $obj = @{
        success = $true
        text = $text
        line_count = $lines.Count
        lines = $lines
    }
    $json = $obj | ConvertTo-Json -Compress
    Write-Output $json
}
catch {
    $errObj = @{
        success = $false
        error = $_.Exception.Message
    }
    Write-Output ($errObj | ConvertTo-Json -Compress)
}
