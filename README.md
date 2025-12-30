# HEIC Location Extractor

HEICファイルから位置情報を抽出してTXTに保存。

## 使い方

### 方法1: ドラッグ&ドロップ
HEICファイルが入ったフォルダを`heic_location_extractor.exe`にドロップ

### 方法2: 同じフォルダに置く
EXEをHEICファイルと同じフォルダに置いてダブルクリック

## 出力
`location_data.txt` が作成される
```
IMG_0001.HEIC,35.681236,139.767125
IMG_0002.HEIC,34.693738,135.502165
```

## ビルド (Windows)
```
rustup (https://rustup.rs) をインストール後:
cargo build --release
→ target\release\heic_location_extractor.exe
```
