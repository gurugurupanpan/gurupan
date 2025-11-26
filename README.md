# gurupan

地理情報付きHEIC写真をGoogle Earth Proにアップロードするためのツール

## 概要

このプロジェクトは、HEIC形式の地理情報付き写真を含むフォルダから、Google Earth Pro用のKMLファイルを生成するJupyter Notebookツールです。

## 機能

- HEICファイルからGPS情報（緯度・経度）を抽出
- 写真のメタデータ（撮影日時、カメラ情報）を取得
- Google Earth Pro用のKMLファイルを生成
- HEICをJPGに変換してGoogle Earth Proでの互換性を向上（オプション）
- 写真の位置をマーカーとして地図上に表示
- マーカークリックで写真とメタデータを表示

## セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. Jupyter Notebookの起動

```bash
jupyter notebook geotag_photos_to_earth.ipynb
```

## 使用方法

1. Jupyter Notebookを開く
2. セルを順番に実行してライブラリをインポート
3. 「使用方法」セクションで以下を設定:
   - `PHOTO_FOLDER`: 地理情報付き写真が入っているフォルダのパス
   - `OUTPUT_KML`: 出力するKMLファイルのパス
   - `CONVERT_TO_JPG`: HEICをJPGに変換するか（推奨: True）
   - `JPG_OUTPUT_FOLDER`: JPG変換後の保存先フォルダ
4. セルを実行してKMLファイルを生成
5. Google Earth Proで生成されたKMLファイルを開く

## Google Earth Proでの開き方

1. Google Earth Proを起動
2. メニューから「ファイル」→「開く」を選択
3. 生成された `.kml` ファイルを選択
4. 写真の場所がマーカーとして表示されます
5. マーカーをクリックすると写真とメタデータが表示されます

## 必要なパッケージ

- `pillow-heif`: HEICファイルの読み込み
- `Pillow`: 画像処理とEXIFデータの取得
- `simplekml`: KMLファイルの生成
- `notebook`: Jupyter Notebook環境

## トラブルシューティング

### GPS情報が取得できない場合
- iPhoneの設定で「カメラ」→「位置情報」が有効になっているか確認
- 写真の「プライバシー設定」で位置情報が削除されていないか確認

### Google Earth Proで画像が表示されない場合
- `CONVERT_TO_JPG = True` に設定して実行（HEICは非対応の場合があります）
- 画像パスが正しく設定されているか確認

## ファイル構成

```
gurupan/
├── geotag_photos_to_earth.ipynb  # メインのJupyter Notebook
├── requirements.txt               # 必要なパッケージリスト
└── README.md                      # このファイル
```

## ライセンス

MIT License