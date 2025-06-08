// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
use serde::Serialize;

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[derive(Serialize, Clone)]
struct DependencyStatus {
  iverilog: bool,
  vvp: bool,
  gtkwave: bool,
}

#[tauri::command]
fn check_dependencies() -> DependencyStatus {
  DependencyStatus {
    iverilog: which::which("iverilog").is_ok(),
    vvp: which::which("vvp").is_ok(),
    gtkwave: which::which("gtkwave").is_ok(),
  }
}

#[tauri::command]
fn clean_project(paths: Vec<String>) {
    for path in paths {
        if !path.is_empty() {
            match std::fs::remove_file(&path) {
                Ok(_) => println!("Successfully deleted file: {}", path),
                Err(e) => {
                    // It's okay if the file doesn't exist, so we only log other errors.
                    if e.kind() != std::io::ErrorKind::NotFound {
                        eprintln!("Error deleting file {}: {}", path, e);
                    }
                }
            }
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .invoke_handler(tauri::generate_handler![
            greet, 
            check_dependencies,
            clean_project
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
