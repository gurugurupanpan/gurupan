//! HEIC Location Extractor
//!
//! HEICファイルから位置情報（GPS座標）を抽出し、TXTファイルに保存するツール
//! Windows用EXEとしてビルドし、ダブルクリックで実行できます。

#![cfg_attr(windows, windows_subsystem = "windows")]

use exif::{In, Reader, Tag, Value};
use std::fs::File;
use std::io::{BufReader, Write};
use std::path::Path;
use walkdir::WalkDir;

#[cfg(windows)]
mod windows_dialog {
    use std::path::PathBuf;
    use windows::core::*;
    use windows::Win32::System::Com::*;
    use windows::Win32::UI::Shell::Common::*;
    use windows::Win32::UI::Shell::*;
    use windows::Win32::UI::WindowsAndMessaging::*;

    pub fn pick_folder() -> Option<PathBuf> {
        unsafe {
            // COMを初期化
            CoInitializeEx(None, COINIT_APARTMENTTHREADED).ok()?;

            let dialog: IFileOpenDialog =
                CoCreateInstance(&FileOpenDialog, None, CLSCTX_INPROC_SERVER).ok()?;

            // フォルダ選択モードに設定
            let options = dialog.GetOptions().ok()?;
            dialog
                .SetOptions(options | FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM)
                .ok()?;

            dialog
                .SetTitle(w!("HEICファイルが入っているフォルダを選択"))
                .ok()?;

            // ダイアログを表示
            if dialog.Show(None).is_err() {
                CoUninitialize();
                return None;
            }

            // 選択されたフォルダを取得
            let result = dialog.GetResult().ok()?;
            let path_ptr = result.GetDisplayName(SIGDN_FILESYSPATH).ok()?;
            let path_str = path_ptr.to_string().ok()?;
            CoTaskMemFree(Some(path_ptr.as_ptr() as *mut _));

            CoUninitialize();
            Some(PathBuf::from(path_str))
        }
    }

    pub fn show_message(title: &str, message: &str) {
        unsafe {
            let title_wide: Vec<u16> = title.encode_utf16().chain(std::iter::once(0)).collect();
            let message_wide: Vec<u16> = message.encode_utf16().chain(std::iter::once(0)).collect();
            MessageBoxW(
                None,
                windows::core::PCWSTR(message_wide.as_ptr()),
                windows::core::PCWSTR(title_wide.as_ptr()),
                MB_OK | MB_ICONINFORMATION,
            );
        }
    }
}

#[cfg(not(windows))]
mod windows_dialog {
    use std::path::PathBuf;

    pub fn pick_folder() -> Option<PathBuf> {
        // Linux/macOS: コマンドライン引数またはカレントディレクトリを使用
        std::env::args().nth(1).map(PathBuf::from).or_else(|| {
            println!("使用方法: heic_location_extractor <フォルダパス>");
            println!("または、カレントディレクトリを処理します。");
            std::env::current_dir().ok()
        })
    }

    pub fn show_message(_title: &str, message: &str) {
        println!("{}", message);
    }
}

fn main() {
    // フォルダ選択
    let folder_path = match windows_dialog::pick_folder() {
        Some(path) => path,
        None => {
            windows_dialog::show_message("HEIC Location Extractor", "キャンセルされました。");
            return;
        }
    };

    // 結果を格納するベクタ
    let mut results: Vec<String> = Vec::new();
    let mut processed_count = 0;
    let mut success_count = 0;

    // フォルダ内のHEICファイルを走査
    for entry in WalkDir::new(&folder_path)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        let path = entry.path();
        if is_heic_file(path) {
            processed_count += 1;
            if let Some(location_data) = extract_gps_from_file(path) {
                results.push(location_data);
                success_count += 1;
            }
        }
    }

    if results.is_empty() {
        windows_dialog::show_message(
            "HEIC Location Extractor",
            &format!(
                "処理完了\n\n処理ファイル数: {}\n位置情報が見つかりませんでした。",
                processed_count
            ),
        );
        return;
    }

    // 出力ファイルのパスを決定（選択フォルダ内に保存）
    let output_path = folder_path.join("location_data.txt");

    // TXTファイルに書き込み
    match File::create(&output_path) {
        Ok(mut file) => {
            for line in &results {
                if let Err(e) = writeln!(file, "{}", line) {
                    windows_dialog::show_message(
                        "HEIC Location Extractor",
                        &format!("ファイル書き込みエラー: {}", e),
                    );
                    return;
                }
            }
            windows_dialog::show_message(
                "HEIC Location Extractor",
                &format!(
                    "処理完了！\n\n処理ファイル数: {}\n位置情報抽出成功: {}\n\n出力ファイル:\n{}",
                    processed_count,
                    success_count,
                    output_path.display()
                ),
            );
        }
        Err(e) => {
            windows_dialog::show_message(
                "HEIC Location Extractor",
                &format!("ファイル作成エラー: {}", e),
            );
        }
    }
}

/// ファイルがHEIC形式かどうかをチェック
fn is_heic_file(path: &Path) -> bool {
    if !path.is_file() {
        return false;
    }
    match path.extension() {
        Some(ext) => {
            let ext_lower = ext.to_string_lossy().to_lowercase();
            ext_lower == "heic" || ext_lower == "heif"
        }
        None => false,
    }
}

/// ファイルからGPS情報を抽出
fn extract_gps_from_file(path: &Path) -> Option<String> {
    let file = File::open(path).ok()?;
    let mut reader = BufReader::new(file);

    let exif = Reader::new().read_from_container(&mut reader).ok()?;

    // GPS座標を取得
    let lat = get_gps_coordinate(&exif, Tag::GPSLatitude, Tag::GPSLatitudeRef)?;
    let lon = get_gps_coordinate(&exif, Tag::GPSLongitude, Tag::GPSLongitudeRef)?;

    let filename = path.file_name()?.to_string_lossy();

    // フォーマット: ファイル名,緯度,経度
    Some(format!("{},{:.6},{:.6}", filename, lat, lon))
}

/// GPS座標を度数に変換
fn get_gps_coordinate(exif: &exif::Exif, coord_tag: Tag, ref_tag: Tag) -> Option<f64> {
    let coord_field = exif.get_field(coord_tag, In::PRIMARY)?;
    let ref_field = exif.get_field(ref_tag, In::PRIMARY)?;

    // 度分秒を取得
    let rationals = match &coord_field.value {
        Value::Rational(v) if v.len() >= 3 => v,
        _ => return None,
    };

    let degrees = rationals[0].to_f64();
    let minutes = rationals[1].to_f64();
    let seconds = rationals[2].to_f64();

    // 度数に変換
    let mut decimal = degrees + minutes / 60.0 + seconds / 3600.0;

    // 南緯・西経の場合は負の値に
    let reference = ref_field.display_value().to_string();
    if reference.contains('S') || reference.contains('W') {
        decimal = -decimal;
    }

    Some(decimal)
}
