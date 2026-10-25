
$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$designRoot = Join-Path $root "content\designs"
$exportRoot = Join-Path $root "content\exports\instagram"
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"

if (-not (Test-Path -LiteralPath $chrome)) {
    $chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
}
if (-not (Test-Path -LiteralPath $chrome)) {
    throw "Chrome not found."
}

$ids = @("IG-01","IG-02","IG-03","IG-04","IG-05")
$htmlFiles = @()

foreach ($id in $ids) {
    $folder = Join-Path $designRoot $id
    $slides = @(Get-ChildItem -LiteralPath $folder -Filter "*.html" -File)

    if ($slides.Count -ne 5) {
        throw ("{0} must contain 5 HTML slides; found {1}." -f $id, $slides.Count)
    }

    $htmlFiles += $slides
}

if ($htmlFiles.Count -ne 25) {
    throw ("Expected 25 HTML slides; found {0}." -f $htmlFiles.Count)
}

New-Item -ItemType Directory -Path $exportRoot -Force | Out-Null

$tempProfile = Join-Path $env:TEMP ("ig-export-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempProfile | Out-Null

try {
    $index = 0

    foreach ($html in $htmlFiles) {
        $index++
        $pngPath = Join-Path $exportRoot ($html.BaseName + ".png")

        if (Test-Path -LiteralPath $pngPath) {
            $bytes = [System.IO.File]::ReadAllBytes($pngPath)
            if ($bytes.Length -lt 24) {
                throw ("Existing PNG is invalid: {0}" -f $pngPath)
            }
            $sig = [System.BitConverter]::ToString($bytes[0..7])
            if ($sig -ne "89-50-4E-47-0D-0A-1A-0A") {
                throw ("Existing file is not PNG: {0}" -f $pngPath)
            }
            Write-Host ("[{0}/25] Preserved existing {1}" -f $index, $html.BaseName)
            continue
        }

        $uri = ([System.Uri]$html.FullName).AbsoluteUri
        $argsList = @(
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--window-size=1080,1350",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=1200",
            "--user-data-dir=$tempProfile",
            "--screenshot=$pngPath",
            $uri
        )

        Write-Host ("[{0}/25] Exporting {1}" -f $index, $html.BaseName)

        # Start-Process avoids PowerShell interpreting Chrome's stderr text
        # as a terminating native-command error.
        $proc = Start-Process -FilePath $chrome `
            -ArgumentList $argsList `
            -PassThru -Wait -WindowStyle Hidden

        if ($proc.ExitCode -ne 0) {
            throw ("Chrome failed for {0}; exit code {1}" -f $html.Name, $proc.ExitCode)
        }

        if (-not (Test-Path -LiteralPath $pngPath)) {
            throw ("PNG was not created: {0}" -f $pngPath)
        }

        $bytes = [System.IO.File]::ReadAllBytes($pngPath)
        if ($bytes.Length -lt 24) {
            throw ("PNG too small: {0}" -f $pngPath)
        }

        $sig = [System.BitConverter]::ToString($bytes[0..7])
        if ($sig -ne "89-50-4E-47-0D-0A-1A-0A") {
            throw ("PNG signature invalid: {0}" -f $pngPath)
        }

        $width = [System.Net.IPAddress]::NetworkToHostOrder(
            [System.BitConverter]::ToInt32([byte[]]$bytes[16..19], 0)
        )
        $height = [System.Net.IPAddress]::NetworkToHostOrder(
            [System.BitConverter]::ToInt32([byte[]]$bytes[20..23], 0)
        )

        if (($width -ne 1080) -or ($height -ne 1350)) {
            throw ("Wrong dimensions for {0}: {1}x{2}" -f $html.Name, $width, $height)
        }
    }
}
finally {
    if (Test-Path -LiteralPath $tempProfile) {
        Remove-Item -LiteralPath $tempProfile -Recurse -Force -ErrorAction SilentlyContinue
    }
}

$verified = 0
foreach ($html in $htmlFiles) {
    $path = Join-Path $exportRoot ($html.BaseName + ".png")
    if (-not (Test-Path -LiteralPath $path)) {
        throw ("Missing export: {0}" -f $path)
    }

    $bytes = [System.IO.File]::ReadAllBytes($path)
    if ($bytes.Length -lt 24) {
        throw ("Invalid PNG: {0}" -f $path)
    }

    $sig = [System.BitConverter]::ToString($bytes[0..7])
    if ($sig -ne "89-50-4E-47-0D-0A-1A-0A") {
        throw ("Invalid PNG signature: {0}" -f $path)
    }

    $width = [System.Net.IPAddress]::NetworkToHostOrder(
        [System.BitConverter]::ToInt32([byte[]]$bytes[16..19], 0)
    )
    $height = [System.Net.IPAddress]::NetworkToHostOrder(
        [System.BitConverter]::ToInt32([byte[]]$bytes[20..23], 0)
    )

    if (($width -ne 1080) -or ($height -ne 1350)) {
        throw ("Invalid dimensions for {0}: {1}x{2}" -f $path, $width, $height)
    }
    $verified++
}

$count = @(Get-ChildItem -LiteralPath $exportRoot -Filter "*.png" -File).Count

if (($verified -ne 25) -or ($count -ne 25)) {
    throw ("Verification failed: valid={0}, total PNG files={1}" -f $verified, $count)
}

Write-Host ""
Write-Host "PASS: All 25 PNGs verified at 1080 x 1350." -ForegroundColor Green
Write-Host ("Export folder: {0}" -f $exportRoot)
Write-Host "HTML sources preserved."
