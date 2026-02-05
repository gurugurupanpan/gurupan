#!/usr/bin/env python3
"""
写真GPS抽出ツール（GUI版）

フォルダを選択するだけで、写真からGPS位置情報を抽出してCSVファイルに保存します。
HEIC/HEIF形式にも対応しています。
"""

import os
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# HEIC/HEIF対応
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False


class GPSExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("写真GPS抽出ツール")
        self.root.geometry("500x450")
        self.root.resizable(True, True)

        self.setup_ui()

    def setup_ui(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # タイトル
        title_label = ttk.Label(
            main_frame,
            text="📷 写真GPS抽出ツール",
            font=("", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 説明
        desc_label = ttk.Label(
            main_frame,
            text="写真フォルダを選択すると、GPS位置情報をTXTファイルに保存します\n"
                 "対応形式: JPG, PNG, TIFF" + (", HEIC/HEIF" if HEIC_SUPPORTED else ""),
            wraplength=450,
            justify=tk.CENTER
        )
        desc_label.pack(pady=(0, 20))

        # フォルダ選択フレーム
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=5)

        ttk.Label(folder_frame, text="写真フォルダ:").pack(anchor=tk.W)

        entry_frame = ttk.Frame(folder_frame)
        entry_frame.pack(fill=tk.X, pady=5)

        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(entry_frame, textvariable=self.folder_var, width=50)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(entry_frame, text="参照...", command=self.browse_folder)
        browse_btn.pack(side=tk.RIGHT)

        # 実行ボタン
        self.run_btn = ttk.Button(
            main_frame,
            text="🚀 抽出開始",
            command=self.start_extraction
        )
        self.run_btn.pack(pady=20)

        # プログレスバー
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)

        # ステータス
        self.status_var = tk.StringVar(value="フォルダを選択してください")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=5)

        # ログ表示エリア
        log_frame = ttk.LabelFrame(main_frame, text="処理ログ", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_folder(self):
        folder = filedialog.askdirectory(title="写真フォルダを選択")
        if folder:
            self.folder_var.set(folder)
            self.status_var.set("準備完了 - 「抽出開始」をクリック")

    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    def start_extraction(self):
        folder = self.folder_var.get()
        if not folder:
            messagebox.showwarning("警告", "フォルダを選択してください")
            return

        if not os.path.isdir(folder):
            messagebox.showerror("エラー", "指定されたフォルダが見つかりません")
            return

        self.run_btn.configure(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("処理中...")
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

        # バックグラウンドで実行
        thread = threading.Thread(target=self.extract_gps, args=(folder,))
        thread.daemon = True
        thread.start()

    def extract_gps(self, folder_path):
        try:
            # ファイル名: <フォルダ名>_gps_data_<日付>.csv
            folder_name = os.path.basename(folder_path)
            date_str = datetime.now().strftime("%Y%m%d")
            output_filename = f"{folder_name}_gps_data_{date_str}.csv"
            output_file = os.path.join(folder_path, output_filename)

            image_extensions = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
            if HEIC_SUPPORTED:
                image_extensions.update({".heic", ".heif"})

            # 1回目: ファイル情報を収集し、最大フォルダ階層を計算
            file_data = []
            max_depth = 0
            processed = 0
            found = 0

            self.log(f"フォルダを探索中: {folder_path}")
            self.log("")

            for root, dirs, files in os.walk(folder_path):
                for filename in files:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in image_extensions:
                        continue

                    file_path = os.path.join(root, filename)
                    processed += 1

                    self.root.after(0, lambda p=processed: self.status_var.set(f"処理中... {p}枚"))

                    exif_data = self.get_exif_data(file_path)
                    gps_info = self.get_gps_info(exif_data)
                    lat, lon = self.get_lat_lon(gps_info)
                    date_taken = self.get_date_taken(exif_data)

                    rel_path = os.path.relpath(file_path, folder_path)
                    # パスを分割（フォルダ + ファイル名）
                    path_parts = rel_path.replace("\\", "/").split("/")
                    max_depth = max(max_depth, len(path_parts))

                    if lat is not None and lon is not None:
                        found += 1
                        file_data.append((path_parts, f"{lat:.6f}", f"{lon:.6f}", date_taken))
                        self.log(f"✓ {rel_path}: {lat:.6f}, {lon:.6f}")
                    else:
                        file_data.append((path_parts, "緯度経度なし", "", date_taken))
                        self.log(f"✗ {rel_path}: GPS情報なし")

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

            self.log("")
            self.log("=" * 40)
            self.log(f"処理完了!")
            self.log(f"処理した画像: {processed}枚")
            self.log(f"GPS情報あり: {found}枚")
            self.log(f"出力ファイル: {output_file}")

            self.root.after(0, lambda: self.status_var.set(f"完了! {found}/{processed}枚のGPS情報を抽出"))

            self.root.after(0, lambda: messagebox.showinfo(
                "完了",
                f"処理が完了しました！\n\n"
                f"処理した画像: {processed}枚\n"
                f"GPS情報あり: {found}枚\n\n"
                f"出力ファイル:\n{output_file}"
            ))

        except Exception as e:
            self.log(f"エラー: {e}")
            self.root.after(0, lambda: self.status_var.set("エラーが発生しました"))
            self.root.after(0, lambda: messagebox.showerror("エラー", str(e)))

        finally:
            self.root.after(0, self.finish_extraction)

    def finish_extraction(self):
        self.progress.stop()
        self.run_btn.configure(state=tk.NORMAL)

    def get_exif_data(self, image_path):
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
            return {}

    def get_gps_info(self, exif_data):
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

    def get_lat_lon(self, gps_info):
        if not gps_info:
            return None, None

        lat = None
        lon = None

        if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
            lat = self.convert_to_degrees(gps_info["GPSLatitude"])
            if gps_info["GPSLatitudeRef"] == "S":
                lat = -lat

        if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
            lon = self.convert_to_degrees(gps_info["GPSLongitude"])
            if gps_info["GPSLongitudeRef"] == "W":
                lon = -lon

        return lat, lon

    def convert_to_degrees(self, value):
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)

    def get_date_taken(self, exif_data):
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


def main():
    root = tk.Tk()
    app = GPSExtractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
