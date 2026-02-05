# 写真GPS抽出ツール

写真フォルダからGPS位置情報を抽出してTXTファイルに保存するツールです。

## 対応フォーマット
- JPG / JPEG
- PNG
- TIFF
- **HEIC / HEIF** (iPhone写真)

---

## 使い方

### 方法1: EXEファイルを使う（初心者向け）

1. `build_exe.bat` をダブルクリック
2. 作成された `dist\写真GPS抽出ツール.exe` を好きな場所にコピー
3. EXEをダブルクリックして起動
4. 「参照...」ボタンで写真フォルダを選択
5. 「抽出開始」をクリック
6. フォルダ内に `gps_data.txt` が作成されます

### 方法2: Pythonスクリプトを直接実行

```bash
# ライブラリをインストール
pip install -r requirements.txt

# GUI版を起動
python extract_photo_gps_gui.py

# またはコマンドライン版
python extract_photo_gps.py <写真フォルダ> [出力ファイル名]
```

### 方法3: PowerShell（Windows標準機能のみ）

```powershell
.\extract_photo_gps.ps1 -FolderPath "C:\Photos"
```
※ HEIC非対応

---

## 出力ファイル形式

`gps_data.txt` はタブ区切りテキストファイルです：

```
# ファイル名	緯度	経度
IMG_0001.jpg	35.681236	139.767125
IMG_0002.jpg	35.658034	139.701636
旅行/photo.jpg	34.693738	135.502165
```

---

## 必要環境

### EXEを作成する場合
- Python 3.8以上
- Windows 10/11

### EXEを使う場合
- Windows 10/11（Pythonは不要）
