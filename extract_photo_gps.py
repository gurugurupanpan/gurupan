#!/usr/bin/env python3
"""
写真からGPS位置情報を抽出してCSVファイルに保存するスクリプト

使い方:
    python extract_photo_gps.py <写真フォルダのパス>

例:
    python extract_photo_gps.py ./photos
"""

import os
import sys
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# HEIC/HEIF対応
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False


def get_exif_data(image_path: str) -> dict:
    """画像からEXIFデータを取得する"""
    try:
        image = Image.open(image_path)

        # 方法1: getexif() を試す (Pillow 6.0+ / HEIC対応)
        exif_obj = image.getexif()
        if exif_obj:
            exif = {}
            for tag_id, value in exif_obj.items():
                tag = TAGS.get(tag_id, tag_id)
                exif[tag] = value

            # GPSInfo は IFD (Image File Directory) から取得
            if hasattr(exif_obj, 'get_ifd'):
                gps_ifd = exif_obj.get_ifd(0x8825)  # GPSInfo tag
                if gps_ifd:
                    exif["GPSInfo"] = dict(gps_ifd)

            if exif:
                return exif

        # 方法2: _getexif() を試す (従来の方法)
        exif_data = image._getexif()
        if exif_data:
            exif = {}
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                exif[tag] = value
            return exif

        return {}
    except Exception as e:
        print(f"警告: {image_path} のEXIF取得に失敗: {e}")
        return {}


def get_gps_info(exif_data: dict) -> dict:
    """EXIFデータからGPS情報を取得する"""
    if "GPSInfo" not in exif_data:
        return {}

    gps_data = exif_data["GPSInfo"]

    # GPSInfoが辞書でない場合はスキップ
    if not isinstance(gps_data, dict):
        return {}

    gps_info = {}
    for key, value in gps_data.items():
        tag = GPSTAGS.get(key, key)
        gps_info[tag] = value
    return gps_info


def convert_to_degrees(value) -> float:
    """GPS座標を度数に変換する"""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)


def get_lat_lon(gps_info: dict) -> tuple:
    """GPS情報から緯度・経度を取得する"""
    if not gps_info:
        return None, None

    lat = None
    lon = None

    if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
        lat = convert_to_degrees(gps_info["GPSLatitude"])
        if gps_info["GPSLatitudeRef"] == "S":
            lat = -lat

    if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
        lon = convert_to_degrees(gps_info["GPSLongitude"])
        if gps_info["GPSLongitudeRef"] == "W":
            lon = -lon

    return lat, lon


def get_date_taken(exif_data: dict) -> str:
    """撮影日時を取得する"""
    # DateTimeOriginal (撮影日時) を優先
    date_str = exif_data.get("DateTimeOriginal")
    if not date_str:
        # DateTime (更新日時) をフォールバック
        date_str = exif_data.get("DateTime")
    if not date_str:
        return ""

    try:
        # EXIF形式: "2025:01:11 14:30:00" → "2025/01/11 14:30:00"
        return str(date_str).replace(":", "/", 2)
    except:
        return str(date_str)


def extract_gps_from_photos(folder_path: str):
    """フォルダ内の全写真からGPS情報を抽出してCSVファイルに保存する"""

    # ファイル名: <フォルダ名>_gps_data_<日付>.csv
    folder_name = os.path.basename(folder_path)
    date_str = datetime.now().strftime("%Y%m%d")
    output_filename = f"{folder_name}_gps_data_{date_str}.csv"
    output_file = os.path.join(folder_path, output_filename)

    # 対応する画像拡張子
    image_extensions = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic", ".heif"}

    # 1回目: ファイル情報を収集し、最大フォルダ階層を計算
    file_data = []
    max_depth = 0
    processed = 0
    found = 0

    # フォルダ内のファイルを走査
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in image_extensions:
                continue

            file_path = os.path.join(root, filename)
            processed += 1

            # EXIF取得
            exif_data = get_exif_data(file_path)
            gps_info = get_gps_info(exif_data)
            lat, lon = get_lat_lon(gps_info)
            date_taken = get_date_taken(exif_data)

            rel_path = os.path.relpath(file_path, folder_path)
            # パスを分割（フォルダ + ファイル名）
            path_parts = rel_path.replace("\\", "/").split("/")
            max_depth = max(max_depth, len(path_parts))

            if lat is not None and lon is not None:
                found += 1
                file_data.append((path_parts, f"{lat:.6f}", f"{lon:.6f}", date_taken))
                print(f"✓ {rel_path}: {lat:.6f}, {lon:.6f}")
            else:
                file_data.append((path_parts, "緯度経度なし", "", date_taken))
                print(f"✗ {rel_path}: GPS情報なし")

    # 2回目: ファイル出力（UTF-8 BOM付きでExcel対応）
    with open(output_file, "w", encoding="utf-8-sig") as f:
        # ヘッダー行
        headers = [f"フォルダ{i+1}" for i in range(max_depth - 1)] + ["ファイル名", "緯度", "経度", "撮影日時"]
        f.write(",".join(headers) + "\n")

        # データ行
        for path_parts, lat, lon, date_taken in file_data:
            # フォルダ部分を列数に合わせてパディング
            folders = path_parts[:-1]  # フォルダ部分
            filename = path_parts[-1]   # ファイル名
            padded_folders = folders + [""] * (max_depth - 1 - len(folders))
            row = padded_folders + [filename, lat, lon, date_taken]
            f.write(",".join(row) + "\n")

    print(f"\n処理完了:")
    print(f"  処理した画像: {processed}枚")
    print(f"  GPS情報あり: {found}枚")
    print(f"  出力ファイル: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("使い方: python extract_photo_gps.py <写真フォルダのパス>")
        print("例: python extract_photo_gps.py ./photos")
        sys.exit(1)

    folder_path = sys.argv[1]

    if not os.path.isdir(folder_path):
        print(f"エラー: フォルダが見つかりません: {folder_path}")
        sys.exit(1)

    extract_gps_from_photos(folder_path)


if __name__ == "__main__":
    main()
