<#
.SYNOPSIS
    写真からGPS位置情報を抽出してTXTファイルに保存するスクリプト

.DESCRIPTION
    指定フォルダ内の画像ファイルからEXIF GPS情報を抽出し、
    タブ区切りのTXTファイルに出力します。

.PARAMETER FolderPath
    写真が格納されているフォルダのパス

.PARAMETER OutputFile
    出力ファイル名（デフォルト: gps_data.txt）

.EXAMPLE
    .\extract_photo_gps.ps1 -FolderPath "C:\Photos"
    .\extract_photo_gps.ps1 -FolderPath ".\photos" -OutputFile "output.txt"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$FolderPath,

    [Parameter(Mandatory=$false)]
    [string]$OutputFile = "gps_data.txt"
)

Add-Type -AssemblyName System.Drawing

# GPS座標を度数に変換する関数
function Convert-GpsToDecimal {
    param([byte[]]$bytes)

    # EXIF GPS座標は Rational 形式 (分子/分母) × 3 (度/分/秒)
    $deg_num = [BitConverter]::ToUInt32($bytes, 0)
    $deg_den = [BitConverter]::ToUInt32($bytes, 4)
    $min_num = [BitConverter]::ToUInt32($bytes, 8)
    $min_den = [BitConverter]::ToUInt32($bytes, 12)
    $sec_num = [BitConverter]::ToUInt32($bytes, 16)
    $sec_den = [BitConverter]::ToUInt32($bytes, 20)

    $degrees = $deg_num / $deg_den
    $minutes = $min_num / $min_den
    $seconds = $sec_num / $sec_den

    return $degrees + ($minutes / 60) + ($seconds / 3600)
}

# 画像からGPS情報を取得する関数
function Get-PhotoGps {
    param([string]$ImagePath)

    try {
        $image = [System.Drawing.Image]::FromFile($ImagePath)
        $propertyItems = $image.PropertyItems

        $latRef = $null
        $lat = $null
        $lonRef = $null
        $lon = $null

        foreach ($prop in $propertyItems) {
            switch ($prop.Id) {
                # GPSLatitudeRef (N/S)
                1 { $latRef = [System.Text.Encoding]::ASCII.GetString($prop.Value).Trim("`0") }
                # GPSLatitude
                2 { $lat = Convert-GpsToDecimal -bytes $prop.Value }
                # GPSLongitudeRef (E/W)
                3 { $lonRef = [System.Text.Encoding]::ASCII.GetString($prop.Value).Trim("`0") }
                # GPSLongitude
                4 { $lon = Convert-GpsToDecimal -bytes $prop.Value }
            }
        }

        $image.Dispose()

        if ($lat -and $lon -and $latRef -and $lonRef) {
            if ($latRef -eq "S") { $lat = -$lat }
            if ($lonRef -eq "W") { $lon = -$lon }

            return @{
                Latitude = $lat
                Longitude = $lon
            }
        }

        return $null
    }
    catch {
        Write-Warning "警告: $ImagePath の処理に失敗: $_"
        return $null
    }
}

# メイン処理
$FolderPath = Resolve-Path $FolderPath -ErrorAction Stop

$extensions = @("*.jpg", "*.jpeg", "*.png", "*.tiff", "*.tif")
$results = @()
$processed = 0
$found = 0

Write-Host "フォルダを探索中: $FolderPath" -ForegroundColor Cyan

foreach ($ext in $extensions) {
    $files = Get-ChildItem -Path $FolderPath -Filter $ext -Recurse -File -ErrorAction SilentlyContinue

    foreach ($file in $files) {
        $processed++
        $gps = Get-PhotoGps -ImagePath $file.FullName
        $relativePath = $file.FullName.Substring($FolderPath.Path.Length + 1)

        if ($gps) {
            $found++
            $lat = [math]::Round($gps.Latitude, 6)
            $lon = [math]::Round($gps.Longitude, 6)
            $results += "$relativePath`t$lat`t$lon"
            Write-Host "✓ ${relativePath}: $lat, $lon" -ForegroundColor Green
        }
        else {
            Write-Host "✗ ${relativePath}: GPS情報なし" -ForegroundColor Gray
        }
    }
}

# ファイルに書き出し
$output = @("# ファイル名`t緯度`t経度") + $results
$output | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host ""
Write-Host "処理完了:" -ForegroundColor Cyan
Write-Host "  処理した画像: $processed 枚"
Write-Host "  GPS情報あり: $found 枚"
Write-Host "  出力ファイル: $OutputFile"
