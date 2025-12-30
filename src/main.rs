//! HEIC Location Extractor
//! フォルダをEXEにドラッグ&ドロップ、または同じフォルダに置いて実行

use exif::{In, Reader, Tag, Value};
use std::fs::File;
use std::io::{BufReader, Write};
use std::path::Path;
use walkdir::WalkDir;

fn main() {
    // コマンドライン引数からフォルダパスを取得（ドラッグ&ドロップ対応）
    // 引数がなければEXEと同じフォルダを処理
    let folder_path = std::env::args()
        .nth(1)
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|| std::env::current_dir().unwrap());

    println!("処理フォルダ: {}", folder_path.display());

    let mut results: Vec<String> = Vec::new();
    let mut processed = 0;

    for entry in WalkDir::new(&folder_path).into_iter().filter_map(|e| e.ok()) {
        let path = entry.path();
        if is_heic(path) {
            processed += 1;
            if let Some(data) = extract_gps(path) {
                results.push(data);
            }
        }
    }

    let output_path = folder_path.join("location_data.txt");

    if results.is_empty() {
        println!("\n処理ファイル: {}件\n位置情報なし", processed);
    } else {
        let mut file = File::create(&output_path).expect("ファイル作成エラー");
        for line in &results {
            writeln!(file, "{}", line).expect("書き込みエラー");
        }
        println!(
            "\n処理ファイル: {}件\n位置情報抽出: {}件\n出力: {}",
            processed,
            results.len(),
            output_path.display()
        );
    }

    // Enterキー待ち（コンソールがすぐ閉じないように）
    println!("\nEnterキーで終了...");
    let mut buf = String::new();
    std::io::stdin().read_line(&mut buf).ok();
}

fn is_heic(path: &Path) -> bool {
    path.is_file()
        && path
            .extension()
            .map(|e| {
                let e = e.to_string_lossy().to_lowercase();
                e == "heic" || e == "heif"
            })
            .unwrap_or(false)
}

fn extract_gps(path: &Path) -> Option<String> {
    let file = File::open(path).ok()?;
    let exif = Reader::new().read_from_container(&mut BufReader::new(file)).ok()?;

    let lat = get_coord(&exif, Tag::GPSLatitude, Tag::GPSLatitudeRef)?;
    let lon = get_coord(&exif, Tag::GPSLongitude, Tag::GPSLongitudeRef)?;
    let name = path.file_name()?.to_string_lossy();

    Some(format!("{},{:.6},{:.6}", name, lat, lon))
}

fn get_coord(exif: &exif::Exif, tag: Tag, ref_tag: Tag) -> Option<f64> {
    let field = exif.get_field(tag, In::PRIMARY)?;
    let ref_field = exif.get_field(ref_tag, In::PRIMARY)?;

    let r = match &field.value {
        Value::Rational(v) if v.len() >= 3 => v,
        _ => return None,
    };

    let mut val = r[0].to_f64() + r[1].to_f64() / 60.0 + r[2].to_f64() / 3600.0;

    let dir = ref_field.display_value().to_string();
    if dir.contains('S') || dir.contains('W') {
        val = -val;
    }
    Some(val)
}
