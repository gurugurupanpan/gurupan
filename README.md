# gurupan

地理情報付き写真をGoogle Earth Proにアップロードするツール

## 概要

このツールは、フォルダ内の地理情報(GPS)付き写真から自動的にKMLファイルを生成し、Google Earth Proで簡単に表示できるようにします。

## 機能

- 写真のEXIFデータからGPS情報を自動抽出
- 緯度・経度・高度情報を含むKMLファイルの生成
- 写真のサムネイルをGoogle Earth Pro上に表示
- 撮影日時などのメタデータ表示
- 大量の写真を一度に処理可能

## 必要なもの

- Python 3.7以上
- Google Earth Pro（無料でダウンロード可能）

## インストール

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/gurupan.git
cd gurupan
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

または個別にインストール:

```bash
pip install Pillow simplekml
```

## 使い方

### 基本的な使用方法

```bash
python photo_to_kml.py <写真フォルダのパス>
```

例:
```bash
python photo_to_kml.py ./my_vacation_photos
```

これで`photos.kml`というファイルが生成されます。

### 出力ファイル名を指定する場合

```bash
python photo_to_kml.py <写真フォルダのパス> <出力KMLファイル名>
```

例:
```bash
python photo_to_kml.py ./my_vacation_photos vacation_2024.kml
```

### Google Earth Proで開く

1. 生成された`.kml`ファイルをダブルクリック
2. またはGoogle Earth Proを開いて「ファイル」→「開く」から選択

## 詳細手順

### ステップ1: 写真を準備

1. GPS情報付きの写真を1つのフォルダにまとめます
2. サポートされる形式:
   - JPEG (.jpg, .jpeg)
   - PNG (.png)
   - TIFF (.tif, .tiff)

### ステップ2: KMLファイルを生成

```bash
python photo_to_kml.py /path/to/your/photos
```

実行すると、以下の情報が表示されます:
```
処理中: IMG_001.jpg
処理中: IMG_002.jpg
  スキップ: GPS情報なし
処理中: IMG_003.jpg

完了!
  処理した写真: 2枚
  スキップ: 1枚
  出力ファイル: photos.kml

Google Earth Proで 'photos.kml' を開いてください
```

### ステップ3: Google Earth Proで表示

1. **Google Earth Proを起動**

2. **KMLファイルを開く**
   - ファイルをダブルクリック、または
   - Google Earth Pro内で「ファイル」→「開く」→生成したKMLファイルを選択

3. **写真を確認**
   - 地図上にカメラアイコンが表示されます
   - アイコンをクリックすると写真のサムネイルと詳細情報が表示されます

## トラブルシューティング

### GPS情報がない写真について

一部の写真にGPS情報がない場合、以下のメッセージが表示されます:
```
スキップ: GPS情報なし
```

これは正常な動作です。GPS情報がない写真はKMLファイルに含まれません。

### GPS情報の確認方法

写真にGPS情報があるか確認するには:
- **Windows**: 写真を右クリック → プロパティ → 詳細タブ → GPS情報を確認
- **Mac**: 写真を選択 → ⌘+I → 詳細情報 → 位置情報を確認
- **スマートフォン**: カメラアプリで位置情報サービスが有効になっているか確認

### Google Earth Proで写真が表示されない

画像パスが正しく認識されない場合があります。その場合:
1. KMLファイルと写真を同じフォルダに配置
2. 相対パスを使用したい場合は、スクリプトの修正が必要です

## 高度な使用方法

### スクリプトをPythonコードから使用

```python
from photo_to_kml import create_kml_from_photos

# KMLファイルを生成
create_kml_from_photos(
    photo_dir='./my_photos',
    output_kml='output.kml',
    icon_scale=1.5  # アイコンを1.5倍に拡大
)
```

### KMLファイルの構造

生成されるKMLファイルには以下の情報が含まれます:
- プレースマーク名: 写真ファイル名
- 座標: 緯度、経度、高度
- 説明: 画像プレビュー、撮影日時、ファイルパス

## Google Earth Proのダウンロード

Google Earth Proは無料で利用できます:
https://www.google.com/earth/versions/#earth-pro

## サポートされる環境

- Windows 10/11
- macOS 10.14以降
- Linux (Ubuntu, Debian等)

## ライセンス

MIT License

## 貢献

プルリクエストや問題報告を歓迎します！

## 参考情報

### GPS付き写真の撮影方法

- **スマートフォン**:
  - カメラアプリで位置情報サービスを有効にする
  - 設定 → プライバシー → 位置情報サービス → カメラをON

- **デジタルカメラ**:
  - GPS機能付きカメラを使用
  - またはスマートフォンとペアリングしてGPS情報を記録

### KMLファイルの活用

- Google Earth Proだけでなく、Google MapsやGoogle Earth Webでも開けます
- 複数のKMLファイルを同時に表示可能
- レイヤーとして保存して、後で再度開くことができます

## よくある質問

**Q: 何枚くらいの写真を処理できますか？**
A: 数千枚でも処理可能ですが、Google Earth Proでの表示速度は写真の数に依存します。

**Q: 写真のオリジナルファイルは必要ですか？**
A: はい。KMLファイルは写真への参照を保存するため、オリジナルファイルを移動すると表示されなくなります。

**Q: 動画ファイルは対応していますか？**
A: 現在は静止画像のみ対応しています。

**Q: GPS情報を後から追加できますか？**
A: EXIFエディタツールを使用してGPS情報を手動で追加することは可能ですが、本ツールは既存のGPS情報のみを読み取ります。

## 関連ツール

- [ExifTool](https://exiftool.org/): EXIF情報の編集・確認
- [Google Photos](https://photos.google.com/): クラウド上での写真管理（位置情報も保存）
- [JOSM](https://josm.openstreetmap.de/): OpenStreetMapへの写真アップロード

---

Happy mapping! 🗺️📸
