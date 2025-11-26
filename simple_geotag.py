"""
HEIC写真の地理情報をKMLファイルに変換するシンプルスクリプト
Jupyter Notebook不要で、コマンドプロンプトから直接実行できます

使い方:
  python simple_geotag.py                          # 対話モード
  python simple_geotag.py C:/写真フォルダ           # フォルダを直接指定
  python simple_geotag.py C:/写真/IMG_0001.heic    # 単一ファイルをテスト
"""

import os
import sys
from pathlib import Path

try:
    import pillow_heif
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    import simplekml
    print("✓ すべての必要なパッケージがインストールされています\n")
except ImportError as e:
    print(f"エラー: 必要なパッケージがありません")
    print(f"詳細: {e}\n")
    print("以下のコマンドでインストールしてください:")
    print("python -m pip install pillow-heif pillow simplekml\n")
    input("Enterキーを押して終了...")
    exit(1)

# HEIF形式を登録
pillow_heif.register_heif_opener()


def get_exif_data(image_path):
    """画像ファイルからEXIFデータを取得"""
    try:
        image = Image.open(image_path)
        exif_data = image.getexif()
        return exif_data
    except Exception as e:
        print(f"EXIF読み取りエラー ({image_path}): {e}")
        return None


def get_gps_info(exif_data):
    """EXIFデータからGPS情報を抽出"""
    if not exif_data:
        return None

    gps_info = {}

    for tag_id, value in exif_data.items():
        tag_name = TAGS.get(tag_id, tag_id)
        if tag_name == 'GPSInfo':
            for gps_tag_id, gps_value in value.items():
                gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                gps_info[gps_tag_name] = gps_value
            break

    return gps_info if gps_info else None


def convert_to_degrees(value):
    """GPS座標を度数法に変換"""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)


def get_lat_lon(gps_info):
    """GPS情報から緯度経度を取得"""
    if not gps_info:
        return None, None

    try:
        lat = convert_to_degrees(gps_info.get('GPSLatitude', [0, 0, 0]))
        lon = convert_to_degrees(gps_info.get('GPSLongitude', [0, 0, 0]))

        # 南緯と西経の場合は負の値にする
        if gps_info.get('GPSLatitudeRef') == 'S':
            lat = -lat
        if gps_info.get('GPSLongitudeRef') == 'W':
            lon = -lon

        return lat, lon
    except (KeyError, TypeError, ValueError) as e:
        print(f"GPS座標変換エラー: {e}")
        return None, None


def get_photo_metadata(image_path, exif_data):
    """写真のメタデータを取得"""
    metadata = {
        'filename': os.path.basename(image_path),
        'path': str(image_path)
    }

    if exif_data:
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == 'DateTime':
                metadata['datetime'] = value
            elif tag_name == 'Make':
                metadata['camera_make'] = value
            elif tag_name == 'Model':
                metadata['camera_model'] = value

    return metadata


def test_single_photo(photo_path):
    """単一の写真をテスト"""
    print("=" * 60)
    print("単一写真のテスト")
    print("=" * 60)

    if not os.path.exists(photo_path):
        print(f"エラー: ファイルが見つかりません: {photo_path}")
        return

    print(f"ファイル: {photo_path}")

    exif_data = get_exif_data(photo_path)
    gps_info = get_gps_info(exif_data)
    lat, lon = get_lat_lon(gps_info)
    metadata = get_photo_metadata(photo_path, exif_data)

    print(f"\n📸 ファイル名: {metadata['filename']}")
    print(f"📅 撮影日時: {metadata.get('datetime', 'N/A')}")
    print(f"📷 カメラ: {metadata.get('camera_make', 'N/A')} {metadata.get('camera_model', '')}")

    if lat and lon:
        print(f"📍 緯度: {lat:.6f}")
        print(f"📍 経度: {lon:.6f}")
        print(f"🌏 Google Maps: https://www.google.com/maps?q={lat},{lon}")
        print("\n✓ GPS情報が見つかりました！")
    else:
        print("⚠ GPS情報が見つかりませんでした")


def create_kml_from_folder(photo_folder, output_kml_path, convert_to_jpg=False, jpg_output_folder=None):
    """フォルダ内のすべての写真からKMLを生成"""
    photo_folder = Path(photo_folder)

    if convert_to_jpg and jpg_output_folder:
        jpg_output_folder = Path(jpg_output_folder)
        jpg_output_folder.mkdir(parents=True, exist_ok=True)

    kml = simplekml.Kml()
    kml.document.name = "地理情報付き写真"

    stats = {
        'total_files': 0,
        'with_gps': 0,
        'without_gps': 0,
        'errors': 0
    }

    photo_files = list(photo_folder.glob('*.heic')) + \
                  list(photo_folder.glob('*.HEIC')) + \
                  list(photo_folder.glob('*.heif')) + \
                  list(photo_folder.glob('*.HEIF'))

    print("\n" + "=" * 60)
    print("フォルダ内の写真を処理")
    print("=" * 60)
    print(f"処理開始: {len(photo_files)} 個のHEICファイルを検出\n")

    for photo_path in photo_files:
        stats['total_files'] += 1

        try:
            exif_data = get_exif_data(photo_path)
            gps_info = get_gps_info(exif_data)
            lat, lon = get_lat_lon(gps_info)

            if lat and lon:
                stats['with_gps'] += 1

                metadata = get_photo_metadata(photo_path, exif_data)

                image_reference_path = str(photo_path)
                if convert_to_jpg and jpg_output_folder:
                    jpg_filename = photo_path.stem + '.jpg'
                    jpg_path = jpg_output_folder / jpg_filename

                    img = Image.open(photo_path)
                    img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
                    img.save(jpg_path, 'JPEG', quality=85)

                    image_reference_path = str(jpg_path)
                    print(f"✓ {metadata['filename']} → {jpg_filename} (GPS: {lat:.6f}, {lon:.6f})")
                else:
                    print(f"✓ {metadata['filename']} (GPS: {lat:.6f}, {lon:.6f})")

                pnt = kml.newpoint()
                pnt.name = metadata['filename']
                pnt.coords = [(lon, lat)]

                description = f"""<![CDATA[
                <h3>{metadata['filename']}</h3>
                <img src="file:///{image_reference_path}" width="400"/><br/>
                <b>撮影日時:</b> {metadata.get('datetime', 'N/A')}<br/>
                <b>カメラ:</b> {metadata.get('camera_make', '')} {metadata.get('camera_model', '')}<br/>
                <b>座標:</b> {lat:.6f}, {lon:.6f}
                ]]>"""
                pnt.description = description

                pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/camera.png'

            else:
                stats['without_gps'] += 1
                print(f"⚠ {photo_path.name}: GPS情報なし")

        except Exception as e:
            stats['errors'] += 1
            print(f"✗ {photo_path.name}: エラー - {str(e)}")

    kml.save(output_kml_path)

    print("\n" + "=" * 60)
    print("処理完了!")
    print("=" * 60)
    print(f"\n📄 KMLファイル: {output_kml_path}")
    print(f"\n📊 統計:")
    print(f"  総ファイル数: {stats['total_files']}")
    print(f"  GPS情報あり: {stats['with_gps']}")
    print(f"  GPS情報なし: {stats['without_gps']}")
    print(f"  エラー: {stats['errors']}")

    return stats


def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("HEIC写真 → Google Earth Pro KML変換ツール")
    print("=" * 60)

    # コマンドライン引数でパスが指定された場合
    if len(sys.argv) > 1:
        path = sys.argv[1]

        if os.path.isfile(path):
            # 単一ファイル
            print("\n単一ファイルモード")
            test_single_photo(path)
        elif os.path.isdir(path):
            # フォルダ
            print("\nフォルダ処理モード")
            print(f"フォルダ: {path}\n")

            output_kml = "geotagged_photos.kml"
            convert_to_jpg = True
            jpg_folder = "converted_photos"

            print(f"出力KMLファイル: {output_kml}")
            print(f"JPG変換: はい")
            print(f"JPG保存先: {jpg_folder}\n")

            create_kml_from_folder(path, output_kml, convert_to_jpg, jpg_folder)
            print(f"\n✓ {output_kml} を Google Earth Pro で開いてください！")
        else:
            print(f"\nエラー: パスが見つかりません: {path}")
            print("ファイルまたはフォルダのパスを正しく指定してください")

        print("\n")
        input("Enterキーを押して終了...")
        return

    # 対話モード
    print("\n📁 写真ファイルまたはフォルダのパスを入力してください")
    print("   例: C:/Users/gurug/Documents/IMG_0624.heic")
    print("   例: C:/Users/gurug/Documents/photo")
    print("   (何も入力せずEnterでサンプルパスを使用)")

    path = input("\nパス: ").strip().strip('"')  # ダブルクォートを削除

    if not path:
        # デフォルトパス
        path = "C:/Users/gurug/Documents/IMG_0624.heic"
        print(f"デフォルトパスを使用: {path}")

    if not os.path.exists(path):
        print(f"\nエラー: パスが見つかりません: {path}")
        print("\nパスを確認してください:")
        print("- Windowsの場合、スラッシュは / または \\\\ を使用")
        print("- 例: C:/Users/username/Documents")
        print("- または: C:\\\\Users\\\\username\\\\Documents")
        print("\n")
        input("Enterキーを押して終了...")
        return

    if os.path.isfile(path):
        # 単一ファイル
        print("\n📸 単一ファイルをテストします\n")
        test_single_photo(path)

    elif os.path.isdir(path):
        # フォルダ
        print("\n📁 フォルダ内のすべてのHEIC写真を処理します\n")

        output_kml = input("出力KMLファイル名 [geotagged_photos.kml]: ").strip()
        if not output_kml:
            output_kml = "geotagged_photos.kml"

        convert = input("HEICをJPGに変換しますか? (y/n) [y]: ").strip().lower()
        convert_to_jpg = convert != 'n'

        jpg_folder = None
        if convert_to_jpg:
            jpg_folder = input("JPG保存先フォルダ [converted_photos]: ").strip()
            if not jpg_folder:
                jpg_folder = "converted_photos"

        create_kml_from_folder(path, output_kml, convert_to_jpg, jpg_folder)
        print(f"\n✓ {output_kml} を Google Earth Pro で開いてください！")

    print("\n")
    input("Enterキーを押して終了...")


if __name__ == "__main__":
    main()
