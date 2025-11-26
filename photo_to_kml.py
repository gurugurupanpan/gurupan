#!/usr/bin/env python3
"""
地理情報付き写真からKMLファイルを生成するスクリプト
Google Earth Proで写真を地理情報付きで表示するためのツール
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import simplekml


def get_exif_data(image_path):
    """画像からEXIFデータを取得"""
    try:
        image = Image.open(image_path)
        exif_data = {}

        if hasattr(image, '_getexif'):
            exif_info = image._getexif()
            if exif_info is not None:
                for tag, value in exif_info.items():
                    decoded = TAGS.get(tag, tag)
                    exif_data[decoded] = value

        return exif_data
    except Exception as e:
        print(f"警告: {image_path} のEXIF読み取りエラー: {e}")
        return None


def get_gps_data(exif_data):
    """EXIFデータからGPS情報を取得"""
    if not exif_data or 'GPSInfo' not in exif_data:
        return None

    gps_info = {}
    for key in exif_data['GPSInfo'].keys():
        decode = GPSTAGS.get(key, key)
        gps_info[decode] = exif_data['GPSInfo'][key]

    return gps_info


def convert_to_degrees(value):
    """GPS座標を度数法に変換"""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)


def get_coordinates(gps_data):
    """GPS情報から緯度経度を取得"""
    if not gps_data:
        return None

    try:
        lat = convert_to_degrees(gps_data['GPSLatitude'])
        if gps_data['GPSLatitudeRef'] == 'S':
            lat = -lat

        lon = convert_to_degrees(gps_data['GPSLongitude'])
        if gps_data['GPSLongitudeRef'] == 'W':
            lon = -lon

        # 高度情報（オプション）
        altitude = 0
        if 'GPSAltitude' in gps_data:
            altitude = float(gps_data['GPSAltitude'])
            if 'GPSAltitudeRef' in gps_data and gps_data['GPSAltitudeRef'] == 1:
                altitude = -altitude

        return lat, lon, altitude
    except Exception as e:
        print(f"座標変換エラー: {e}")
        return None


def get_photo_datetime(exif_data):
    """写真の撮影日時を取得"""
    if not exif_data:
        return None

    for key in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
        if key in exif_data:
            try:
                return datetime.strptime(exif_data[key], '%Y:%m:%d %H:%M:%S')
            except:
                pass
    return None


def create_kml_from_photos(photo_dir, output_kml='photos.kml', icon_scale=1.0):
    """
    写真フォルダからKMLファイルを生成

    Args:
        photo_dir: 写真が入っているフォルダパス
        output_kml: 出力するKMLファイル名
        icon_scale: アイコンのスケール（デフォルト: 1.0）
    """
    photo_dir = Path(photo_dir)
    if not photo_dir.exists():
        print(f"エラー: フォルダが見つかりません: {photo_dir}")
        return False

    # KMLオブジェクトを作成
    kml = simplekml.Kml()
    kml.document.name = f"写真コレクション - {photo_dir.name}"

    # サポートする画像形式
    supported_formats = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}

    photo_count = 0
    skipped_count = 0

    # フォルダ内の画像を処理
    for image_path in photo_dir.iterdir():
        if image_path.suffix.lower() not in supported_formats:
            continue

        print(f"処理中: {image_path.name}")

        # EXIF情報を取得
        exif_data = get_exif_data(image_path)
        if not exif_data:
            skipped_count += 1
            continue

        # GPS情報を取得
        gps_data = get_gps_data(exif_data)
        if not gps_data:
            print(f"  スキップ: GPS情報なし")
            skipped_count += 1
            continue

        # 座標を取得
        coords = get_coordinates(gps_data)
        if not coords:
            skipped_count += 1
            continue

        lat, lon, altitude = coords

        # プレースマークを作成
        pnt = kml.newpoint()
        pnt.name = image_path.name
        pnt.coords = [(lon, lat, altitude)]

        # 撮影日時を取得
        photo_datetime = get_photo_datetime(exif_data)

        # 説明を作成（画像を含む）
        description = f"""
        <![CDATA[
        <img src="file:///{image_path.absolute()}" width="400"><br>
        <b>ファイル名:</b> {image_path.name}<br>
        <b>緯度:</b> {lat:.6f}<br>
        <b>経度:</b> {lon:.6f}<br>
        <b>高度:</b> {altitude:.1f}m<br>
        """

        if photo_datetime:
            description += f"<b>撮影日時:</b> {photo_datetime.strftime('%Y年%m月%d日 %H:%M:%S')}<br>"

        description += f"<b>パス:</b> {image_path.absolute()}<br>"
        description += "]]>"

        pnt.description = description

        # アイコンスタイルを設定（カメラアイコン）
        pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/camera.png'
        pnt.style.iconstyle.scale = icon_scale

        photo_count += 1

    if photo_count == 0:
        print("\n警告: GPS情報を持つ写真が見つかりませんでした")
        return False

    # KMLファイルを保存
    kml.save(output_kml)

    print(f"\n完了!")
    print(f"  処理した写真: {photo_count}枚")
    print(f"  スキップ: {skipped_count}枚")
    print(f"  出力ファイル: {output_kml}")
    print(f"\nGoogle Earth Proで '{output_kml}' を開いてください")

    return True


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print(f"  python {sys.argv[0]} <写真フォルダ> [出力KMLファイル名]")
        print("\n例:")
        print(f"  python {sys.argv[0]} ./my_photos")
        print(f"  python {sys.argv[0]} ./my_photos output.kml")
        sys.exit(1)

    photo_dir = sys.argv[1]
    output_kml = sys.argv[2] if len(sys.argv) > 2 else 'photos.kml'

    success = create_kml_from_photos(photo_dir, output_kml)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
