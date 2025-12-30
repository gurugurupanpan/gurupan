# HEIC Location Extractor

HEICファイルから位置情報（GPS座標）を抽出し、TXTファイルに保存するツール。

## 機能

- フォルダ選択ダイアログでHEICファイルが入ったフォルダを選択
- フォルダ内の全HEIC/HEIFファイルを自動検索（サブフォルダ含む）
- 各ファイルからGPS情報を抽出
- `location_data.txt`に結果を保存（1行1データ）

## 出力形式

```
ファイル名,緯度,経度
IMG_0001.HEIC,35.681236,139.767125
IMG_0002.HEIC,34.693738,135.502165
```

## ビルド方法（Windows）

### 1. Rustのインストール
https://rustup.rs/ からRustをインストール

### 2. ビルド
```bash
cargo build --release
```

### 3. EXEの場所
```
target\release\heic_location_extractor.exe
```

## 使い方

1. `heic_location_extractor.exe`をダブルクリック
2. フォルダ選択ダイアログが表示される
3. HEICファイルが入っているフォルダを選択
4. 処理完了後、選択フォルダ内に`location_data.txt`が作成される

## 必要条件

- Windows 10以降
- Rust 1.70以降（ビルド時のみ）
